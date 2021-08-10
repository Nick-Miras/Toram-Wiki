# TODO: Create a class for items that are to be paginated
# TODO:
from types import FunctionType
from . import ui
from discord.ext import menus
import inspect
import discord
from typing import Union, Any
import asyncio
from discord import Interaction, ButtonStyle, SelectOption, InteractionMessage
from discord.ui import button, Select, Item
from discord.ext import commands
from . import database
import time
from bson.binary import Binary, USER_DEFINED_SUBTYPE


class PaginationItem:
    def __init__(self, name, item: Any = None):
        # TODO: Decide whether to have NoneType as the default value of :param item:
        self.name = str(name)
        self.item = item

    def __str__(self):
        return self.name

    def to_dict(self):
        return {self.name: self}

    async def display(self) -> Any:
        """Invoked when you want to display the information.
        """
        raise NotImplementedError

    def __getitem__(self, item):  # TODO: Maybe remove this
        if item == self.name:
            return self


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
        return self.source.get_child(self.source.get_page(self.current_page), item)


class PageSource:

    def __init__(self, data: list[PaginationItem], *, per_page):
        if all(isinstance(item, PaginationItem) is True for item in data) is False:
            raise TypeError(f"Elements in data is not of the same type")
        if self._check_duplicates([item.name for item in data]) is True:
            raise Exception('Data cannot have duplicate names!')
        self.data = data
        self.per_page = per_page

        pages, left_over = divmod(len(data), per_page)
        if left_over:
            pages += 1

        self.max_pages = pages

    @staticmethod
    def _check_duplicates(array: list) -> bool:
        # Returns True if there are duplicates
        for elem in array:
            if array.count(elem) > 1:
                return True
        return False

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

    @staticmethod
    def page_to_dictionary(page: list[PaginationItem]) -> dict:
        # TODO: Maybe turn to generator
        for ele in page:
            yield ele.to_dict()

    def get_child(self, page: list[PaginationItem], item) -> PaginationItem:
        """Returns a child or item of a page
        """  # TODO: Decide whether to change :param page_number: to :param page:
        if isinstance(item, int):
            return page[item]
        if isinstance(item, str):
            for element in self.page_to_dictionary(page):
                # element_name is of the class :dict:
                if item in element:
                    return element[item]


class Dropdown(Select):
    def __init__(self, *, paginator, options: FunctionType, **kwargs):
        if not isinstance(options, FunctionType):
            raise TypeError(f'Expected {FunctionType} not {options.__class__}')
        if 'paginator' not in inspect.signature(options).parameters:
            raise Exception('Missing Argument:`paginator`!')
        options = options(paginator)
        self.paginator = paginator
        self.initialized = True
        super().__init__(options=options, **kwargs)

    @staticmethod
    def fetch_view(interaction_id: int):
        return database.global_dict[interaction_id]

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        paginator = self.paginator
        child: PaginationItem = paginator[self.values[0]]
        view = self.fetch_view(interaction.id)
        await interaction.response.edit_message(content=await child.display(), view=view)  # TODO: Finish


class PaginatorView(discord.ui.View):
    """Implements the Paginator
    """
    # TODO: Add what happens if a user uses `PaginationItem.display()`
    # TODO: Make buttons more customizable
    def __init__(self, ctx, *, paginator: Paginator, options: FunctionType, dropdown: Dropdown = None, timeout=None):
        # TODO: Maybe add an `Options` parameter
        # IMPORTANT NOTE: Paginator must be initialized and Dropdown must not be initialized!
        super().__init__(timeout=timeout)

        if not isinstance(paginator, Paginator):
            raise TypeError(f'Expected {Paginator} not {paginator.__class__}')
        if not isinstance(options, FunctionType):
            raise TypeError(f'Expected {FunctionType} not {options.__class__}')
        if not hasattr(paginator, 'initialized'):
            raise Exception('Paginator is not initialized!')
        if hasattr(dropdown, 'initialized'):
            raise Exception('Dropdown must not be initialized!')

        self.ctx: commands.Context = ctx
        self.paginator = paginator
        self.timeout = timeout
        self.options: FunctionType = options  # not initialized
        self.dropdown: Dropdown = Dropdown if dropdown is None else dropdown
        self._init__dropdown: Dropdown = self.dropdown(paginator=paginator, options=options)  # initialized dropdown
        self.add_item(self._init__dropdown)
        self.buttons = self.children.copy()
        self.message_state_before_callback: discord.Message = None
        self.message_state_after_callback: discord.Message = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    async def _scheduled_task(self, item: Item, interaction: Interaction):
        try:
            if self.timeout:
                self.__timeout_expiry = time.monotonic() + self.timeout

            allow = await self.interaction_check(interaction)
            if not allow:
                return

            self.message_state_before_callback: discord.Message = interaction.message

            await self.on_interaction(item, interaction)  # event
            await item.callback(interaction)
            if not interaction.response._responded:
                await interaction.response.defer()

            self.message_state_after_callback: InteractionMessage = await interaction.original_message()  # TODO: Decide whether to remove this
        except Exception as e:
            return await self.on_error(e, item, interaction)

    async def go_back_callback(self, interaction: discord.Interaction):
        # the callback for the `go back` buttons
        self.clear_items()
        for button in self.buttons:
            self.add_item(button)

        content = self.message_state_before_callback.content
        # NOTE: Won't work if there is another button except the `GO BACK` button
        await interaction.response.edit_message(content=content, view=self)

    async def on_dropdown_select(self, item: discord.ui.Item, interaction: Interaction):
        """This is just for removing the buttons and things in the back-end.
        The front end will be handled by the self.dropdown class.
        """
        if isinstance(item, self.dropdown):
            self.clear_items()
            self.add_item(ui.BetterButton(callback=self.go_back_callback, style=ButtonStyle.grey, emoji='🔙'))
            # TODO: Improve GO BACK Emoji
            database.global_dict[interaction.id] = self

    async def on_interaction(self, item: discord.ui.Item, interaction: discord.Interaction):
        """On Interaction Event"""
        await self.on_dropdown_select(item, interaction)

    @button(emoji="⏮️", style=ButtonStyle.grey)
    async def go_first_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        kwargs = await paginator.show_page(0)
        await self.update_select_buttons(kwargs, interaction)

    @button(emoji="⬅️", style=ButtonStyle.grey)
    async def go_left(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        current_page = paginator.current_page
        kwargs = await paginator.show_page(current_page - 1)
        await self.update_select_buttons(kwargs, interaction)

    @button(emoji="➡️", style=ButtonStyle.grey)
    async def go_right(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        current_page = paginator.current_page
        kwargs = await paginator.show_page(current_page + 1)
        await self.update_select_buttons(kwargs, interaction)

    @button(emoji="⏭️", style=ButtonStyle.grey)
    async def go_last_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        paginator = self.paginator
        max_pages = paginator.source.max_pages
        kwargs = await paginator.show_page(max_pages - 1)  # we subtract one because max_pages doesn't start at 0
        await self.update_select_buttons(kwargs, interaction)

    async def update_select_buttons(self, kwargs, interaction: discord.Interaction):
        """Updates the Select Button Options
        """
        paginator_view = PaginatorView(
            self.ctx, paginator=self.paginator, options=self.options, dropdown=self.dropdown, timeout=self.timeout
        )  # reinitializes the Paginator
        await interaction.response.edit_message(**kwargs, view=paginator_view)

    async def go_to_child(self):
        """What happens if a user uses `PaginationItem.display()`
        """
        pass
