"""
A module of overridden Objects.
"""
import discord
from discord.ext import commands
import types
from typing import Callable, Any, Union


class BetterButton(discord.ui.Button):
    def __init__(self, *, callback: Callable=None, **kwargs):
        super().__init__(**kwargs)
        self._callback = callback

    async def callback(self, interaction: discord.Interaction) -> Union[None, Any]:
        """Can be overridden
        """
        callback = self._callback
        return await callback(interaction) if callback else None
