"""
contains the Paginator class which is the backend for :class:`discord.ui.View`
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Generic, TypeVar

import discord
from pydantic import BaseModel as PydanticBaseModel
from pydantic import validator
from pydantic.generics import GenericModel as PydanticGenericModel

from Utils.generics import has_duplicates


def get_message_data(value) -> Optional[dict[str, Any]]:
    """transforms the data into a :class:`dict` to be used by :class:`discord.Message`
    """
    if isinstance(value, str):
        return {'content': value, 'embed': None}
    if isinstance(value, discord.Embed):
        return {'embed': value, 'content': None}
    return


class PaginationItem(ABC, PydanticBaseModel):
    name: str
    item: Any  # TODO: Check if this should be :class:`dict`

    def __ne__(self, other):
        return self.name != other.name

    def __hash__(self):
        return hash(self.name)

    def to_dict(self):
        return self.dict()

    @abstractmethod
    async def display(self) -> Any:
        """Invoked when you want to display the information."""

    class Config:
        allow_mutation = False


SequenceT = TypeVar('SequenceT')


class PageSource(ABC, PydanticGenericModel, Generic[SequenceT]):
    data: list[SequenceT]
    per_page: int
    max_pages: int

    def __init__(self, data, *, per_page):
        max_pages = self.compute_max_pages(len(data), per_page)
        super().__init__(data=data, per_page=per_page, max_pages=max_pages)

    @validator('data')
    def check_for_duplicate_elements(cls, data: list[SequenceT]):
        if (duplicates := has_duplicates(data))[0] is True:
            raise ValueError(f'Error! Data has duplicates: {duplicates[1]}')
        return data

    def set_attr(self, attr_name: str, value: Any) -> None:
        """
        Using this to set attributes,
        since Pydantic doesn't allow setting attributes that are not declared in the class scope.
        """
        object.__setattr__(self, attr_name, value)

    @staticmethod
    def compute_max_pages(total_elements: int, items_per_page: int):
        pages, left_over = divmod(total_elements, items_per_page)
        if left_over:
            pages += 1

        return pages

    @staticmethod
    def clean_page_number(page_number, max_pages) -> int:
        """creates limits for the page number"""
        if page_number < 1:  # just in case the page number becomes a negative number
            return 0
        if page_number >= max_pages:
            return max_pages - 1
        return page_number

    @abstractmethod
    def get_page(self, page_number) -> list[SequenceT]: ...

    class Config:
        allow_mutation = False


class PaginationItemSource(PageSource[PaginationItem]):

    def get_page(self, page_number) -> list[PaginationItem]:
        """Returns either a single element of the sequence or
        a slice of the sequence.

        If :attr:`per_page` is set to ``1`` then this returns a list that contains only a single
        element. Otherwise it returns at most :attr:`per_page` elements.
        """
        page_number = self.clean_page_number(page_number, self.max_pages)

        if self.per_page == 1:
            return [self.data[page_number]]
        else:
            base = page_number * self.per_page
            return self.data[base:base + self.per_page]

    def get_child(self, page_number: int, item: Union[int, str]) -> PaginationItem:
        """
        Returns
        -------
        :class:`PaginationItem`
            a child or item of a page
        """
        page = self.get_page(page_number)

        if isinstance(item, int):
            return page[item]
        if isinstance(item, str):
            for pagination_item in page:  # type: PaginationItem
                if pagination_item.name == item:
                    return pagination_item
        raise IndexError('Child does not exist')


class Paginator(ABC):
    """front end for :class:`PaginatorSource`"""
    initialized = False

    def __init__(self, source):
        self._source: PageSource = source
        self.current_page = 0
        self.initialized = True

    @property
    def source(self):
        return self._source

    async def change_source(self, source):
        """|coro|

        Changes the :class:`PageSource` to a different one at runtime.

        Once the change has been set, the menu is moved to the first
        page of the new source if it was started. This effectively
        changes the :attr:`current_page` to 0.

        Raises
        --------
        TypeError
            A :class:`PageSource` was not passed.
        """
        if not isinstance(source, PageSource):
            raise TypeError('Expected {0!r} not {1.__class__!r}.'.format(PageSource, source))

        self._source = source
        self.current_page = 0

    @property
    def current_page(self):
        return self._current_page

    @current_page.setter
    def current_page(self, page_number: int):
        if page_number < 0:
            self._current_page = 0
        elif (max_pages := self.source.max_pages) <= page_number:  # if the value surpasses the max pages
            self._current_page = max_pages - 1
        else:
            self._current_page = page_number

    @staticmethod
    @abstractmethod
    async def _format_page(menu: 'Paginator', data: list[PaginationItem]) -> Union[str, discord.Embed]:
        """How each page should look like

        Parameters
        ----------
        menu: :class:`Paginator`
        data:
            The page returned by :meth:`PageSource.get_page`.
            Preferably: :class:`PaginationItem`
        """

    async def fetch_page_format(self, page: list[PaginationItem]) -> dict[str, Union[str, discord.Embed]]:
        """This processes the objects that we get from :param: page using `format_page`.
        Parameters
        ----------
        page:
            The page returned by :meth:`PageSource.get_page`.
            Preferably: :class:`PaginationItem`.

        Returns
        -------
        :class:`dict`
            This dictionary contains the content or the discord.Embed would be used later as the content for
            the message.
        """
        value = await self._format_page(self, page)
        return get_message_data(value)

    async def show_page(self, page_number) -> dict:
        """IMPORTANT NOTE: This is only uses displaying the page(front end)
        and this doesn't involve anything with backend manipulation
        """
        page = self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self.fetch_page_format(page)
        return kwargs

    async def show_next_page(self):
        return await self.show_page(self.current_page + 1)

    async def show_current_page(self):
        return await self.show_page(self.current_page)

    async def show_initial_page(self):
        return await self.show_page(0)

    def __iter__(self):
        return self

    def __next__(self) -> dict:  # No StopIteration
        current_page = self.current_page
        self.current_page += 1
        return asyncio.run(self.show_page(current_page))  # TODO: Find a way to remove this asyncio run
