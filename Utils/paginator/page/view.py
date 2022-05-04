from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional

import discord
from discord import ui, Interaction
from discord.ext.commands import Context as Ctx
from discord.ui import Item

from .tree import PageTreeController, PageDataTree
from ..exceptions import CurrentNodeNotFound


class IPaginatorView(ui.View, ABC):
    def __init__(self, ctx: Ctx, controller: PageTreeController, *, timeout: Optional[float] = 180.0):
        super().__init__(timeout=timeout)
        if controller.current is None:
            raise CurrentNodeNotFound()

        self.ctx = ctx
        self.controller = controller
        self.set_items(controller.current.get_items())

    def set_items(self, children: list[ui.Item]):
        self.clear_items()
        for child in children:
            self.add_item(child)

    async def _scheduled_task(self, item: Item, interaction: Interaction):
        try:
            if self.timeout:
                self.__timeout_expiry = time.monotonic() + self.timeout

            allow = await self.interaction_check(interaction)
            if not allow:
                return

            await item.callback(interaction)
            await self.on_interaction(item, interaction)
        except Exception as e:
            return await self.on_error(interaction, e, item)

    @abstractmethod
    async def interaction_check(self, interaction: Interaction) -> bool:
        pass

    @abstractmethod
    async def on_interaction(self, item: discord.ui.Item, interaction: discord.Interaction):
        """The method called when a user interacts with the :class:`ui.View`"""


class PaginatorView(IPaginatorView):

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    async def on_interaction(self, item: discord.ui.Item, interaction: discord.Interaction):
        """The method called when a user interacts with the :class:`ui.View`"""
        await self.refresh(interaction)

    @staticmethod
    async def set_current_view_with(tree: PageDataTree, view: IPaginatorView, message: discord.Message):
        # use Protocol annotation for :param:`message`
        view.set_items(tree.get_items())
        await message.edit(**tree.get_content(), view=view)

    async def refresh(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.set_current_view_with(self.controller.current, self, interaction.message)
        # await webhook.delete()
