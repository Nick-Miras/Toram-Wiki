"""
contains the front end for the paginator
"""
import time
from abc import ABC, abstractmethod
from typing import Optional, Type, Any

import discord
from discord import Interaction, ButtonStyle, SelectOption
from discord.ext import commands
from discord.ui import button, Select, Item

from Utils import database
from . import ui
from .exceptions import InitializationError
from .paginator import get_message_data, Paginator


class Dropdown(ABC, Select):
    initialized: bool = False

    def __init__(self, *, paginator, **kwargs):
        self.paginator = paginator
        self.initialized = True
        super().__init__(options=self.get_options(paginator), **kwargs)

    @staticmethod
    @abstractmethod
    def get_options(paginator) -> list[SelectOption]: ...

    @staticmethod
    def fetch_view(interaction_id: int):
        return database.global_dict[interaction_id]

    @abstractmethod
    async def display(self) -> Any:
        """This is used to display the child of a dropdown menu"""

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        view = self.fetch_view(interaction.id)
        kwargs = get_message_data(await self.display())
        await interaction.response.edit_message(**kwargs, view=view)


class PaginatorView(discord.ui.View):
    """Implements the Paginator
    """

    # TODO: Make buttons more customizable
    def __init__(self, ctx, *, paginator: Paginator, dropdown: Type[Dropdown], timeout=None):
        """
        IMPORTANT NOTE: Paginator must be initialized and Dropdown must not be initialized!
        """
        super().__init__(timeout=timeout)

        if not isinstance(paginator, Paginator):
            raise TypeError(f'Expected {Paginator} not {paginator.__class__}')

        if paginator.initialized is False:
            raise InitializationError('Paginator must be initialized!')
        if dropdown.initialized is True:
            raise InitializationError('Dropdown must not be initialized!')

        self.ctx: commands.Context = ctx
        self.paginator = paginator
        self.timeout = timeout
        self.dropdown: Type[Dropdown] = dropdown  # uninitialized
        self._init__dropdown: Dropdown = self.dropdown(paginator=paginator)  # initialized dropdown
        self.add_item(self._init__dropdown)
        self.buttons = self.children.copy()
        self.message_before_dropdown_interaction: Optional[discord.Message] = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    async def _scheduled_task(self, item: Item, interaction: Interaction):
        try:
            if self.timeout:
                self.__timeout_expiry = time.monotonic() + self.timeout

            allow = await self.interaction_check(interaction)
            if not allow:
                return

            await self.on_interaction(item, interaction)  # TODO: Maybe Create a Decorator Event for this
            await item.callback(interaction)
            if not interaction.response._responded:
                await interaction.response.defer()

        except Exception as e:
            return await self.on_error(e, item, interaction)

    async def go_back_callback(self, interaction: discord.Interaction):
        # the callback for the `go back` buttons
        self.clear_items()
        for button in self.buttons:
            self.add_item(button)

        prev_message_state = self.message_before_dropdown_interaction

        kwargs = {'content': prev_message_state.content, 'embed': prev_message_state.embeds[0]}
        # NOTE: Won't work if there is another button except the `GO BACK` button
        await interaction.response.edit_message(**kwargs, view=self)

    async def on_dropdown_select(self, item: discord.ui.Item, interaction: Interaction):
        """
        This is just for removing the buttons and things in the back-end.
        The front end will be handled by the self.dropdown class.
        """
        if isinstance(item, self.dropdown):
            self.clear_items()
            self.message_before_dropdown_interaction = interaction.message
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
        paginator_view = PaginatorView(
            self.ctx, paginator=self.paginator, dropdown=self.dropdown, timeout=self.timeout
        )  # re-initializes the Paginator
        await interaction.response.edit_message(**kwargs, view=paginator_view)
