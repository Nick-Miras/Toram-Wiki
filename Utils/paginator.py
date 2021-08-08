# TODO: Create a class for items that are to be paginated
# TODO:
from discord.ext import menus
import discord
from typing import Union, Any
import asyncio
from discord import Interaction, ButtonStyle, SelectOption
from discord.ui import button, Select
from discord.ext import commands


class PaginationItem:
    def __init__(self, name, item: Any = None):
        # TODO: Decide whether to have NoneType as the default value of :param item:
        self.name = name
        self.item = item

    def to_dict(self):
        return {self.name: self}

    async def display(self) -> Any:
        """Invoked when you want to display the information.
        """
        raise NotImplementedError


class Paginator:

    def __init__(self, source):
        self._source: PageSource = source
        self.current_page = 0
        self.initialized = True

    @property
    def source(self):
        return self._source

    @property
    def current_page(self):
        return self._current_page

    @current_page.setter
    def current_page(self, value):
        if value < 0:
            self._current_page = 0
        elif (max_pages := self.source.max_pages) < value:  # if the value surpasses the max pages
            self._current_page = max_pages
        else:
            self._current_page = value

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

    async def _fetch_page_format(self, page: list[PaginationItem]) -> dict:
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
        value = await discord.utils.maybe_coroutine(self.source.format_page, page)
        # since we don't know if format_page will be a coro or not we use this, plus this function also injects the
        # arguments into the function(1st argument), which makes the 2nd and so on.. argument(of :func: maybe_coroutine)
        # to be the arguments of the function(1st argument)
        if isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}

    async def show_page(self, page_number) -> dict:
        """IMPORTANT NOTE: This is only used for displaying the page(front end)
        and this doesn't involve anything with backend manipulation
        """
        page = self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._fetch_page_format(page)
        return kwargs

    async def show_checked_page(self, page_number):  # idk what this even do
        """IMPORTANT NOTE: This is only used for displaying the page(front end)
        and this doesn't involve anything with backend manipulation
        """
        # TODO: Decide whether to use this function or just rely on current_page not surpassing the domain
        max_pages = self.source.max_pages
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                result = await self.show_page(page_number)
            elif max_pages > page_number >= 0:
                result = await self.show_page(page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass
        else:
            return result

    def show_next_page(self) -> dict:  # the same as __next__
        return self.__next__()  # TODO: Decide whether to use __next__ or not

    async def show_current_page(self):
        return await self.show_page(self.current_page)

    async def initial_page(self):
        return await self.show_page(0)

    def __iter__(self):
        return self

    def __next__(self) -> dict:  # No StopIteration
        current_page = self.current_page
        self.current_page += 1
        return asyncio.run(self.show_page(current_page))  # TODO: Find a way to remove this asyncio run

    def __getitem__(self, item):  # basically the same as `source.open_child`
        return self.source.get_child(self.current_page, item)


class PageSource:

    def __init__(self, data: list[PaginationItem], *, per_page):
        if all(isinstance(item, PaginationItem) is True for item in data) is False:
            raise TypeError(f"Elements in data is not of the same type")
        self.data = data
        self.per_page = per_page

        pages, left_over = divmod(len(data), per_page)
        if left_over:
            pages += 1

        self.max_pages = pages

    async def format_page(self, data: list[PaginationItem]):
        """How each page should look like

        Parameters
        ----------
        data:
            The page returned by :meth:`PageSource.get_page`.
            Preferably: :class:`PaginationItem`
        """
        raise NotImplementedError

    def get_page(self, page_number) -> list[PaginationItem]:
        """Returns either a single element of the sequence or
        a slice of the sequence.

        If :attr:`per_page` is set to ``1`` then this returns a list that contains only a single
        element. Otherwise it returns at most :attr:`per_page` elements.
        """
        if self.per_page == 1:
            return [self.data[page_number]]
        else:
            base = page_number * self.per_page
            return self.data[base:base + self.per_page]

    def get_child(self, page_number, item) -> object:
        """Returns a child or item of a page
        """
        page = self.get_page(page_number)
        if isinstance(item, int):
            return page[item]
        # TODO: Do something if :param item: is :class:`str`
        #  maybe will add on :class:`PaginationItem`


class Dropdown(Select):

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')  # TODO: Finish


class PaginatorView(discord.ui.View):
    """Implements the Paginator
    """
    def __init__(self, ctx, *, paginator: Paginator, dropdown: Select = None, timeout=None):
        # IMPORTANT NOTE: Paginator must be initialized
        super().__init__(timeout=timeout)
        if not isinstance(paginator, Paginator):
            raise TypeError(f'Expected {Paginator} not {paginator.__class__}')
        if not isinstance(dropdown, Select) and dropdown is not None:
            raise TypeError(f'Expected {Select} not {dropdown.__class__}')

        if not paginator.initialized:
            raise Exception('Paginator is not initialized!')
        self.ctx: commands.Context = ctx
        self.paginator = paginator
        self.timeout = timeout
        self.dropdown = dropdown

        page = paginator.source.get_page(paginator.current_page)
        options = [
            SelectOption(label=item.name) for item in page
        ]
        _default_dropdown = Dropdown(
            placeholder='See more information about an item...',
            options=options
        )
        self.add_item(self.dropdown if self.dropdown else _default_dropdown)

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    @button(emoji="⏮️", style=ButtonStyle.grey)
    async def go_first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        kwargs = await paginator.show_page(0)
        await self.update(kwargs, interaction)

    @button(emoji="⬅️", style=ButtonStyle.grey)
    async def go_left(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        current_page = paginator.current_page
        kwargs = await paginator.show_page(current_page - 1)
        await self.update(kwargs, interaction)

    @button(emoji="➡️", style=ButtonStyle.grey)
    async def go_right(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        current_page = paginator.current_page
        kwargs = await paginator.show_page(current_page + 1)
        await self.update(kwargs, interaction)

    @button(emoji="⏭️", style=ButtonStyle.grey)
    async def go_last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        max_page = paginator.source.max_pages
        kwargs = await paginator.show_page(max_page)  # TODO: Verify if max_pages index is correct
        await self.update(kwargs, interaction)

    async def update(self, kwargs, interaction: discord.Interaction):
        """Updates the Select Button Options
        """
        paginator_view = PaginatorView(
            self.ctx, paginator=self.paginator, dropdown=self.dropdown, timeout=self.timeout
        )
        await interaction.response.edit_message(**kwargs, view=paginator_view)
