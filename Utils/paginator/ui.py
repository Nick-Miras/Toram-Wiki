"""
A module of overridden Objects.
"""
from typing import Callable, Any, Union

import discord


class BetterButton(discord.ui.Button):
    def __init__(self, *, callback: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self._callback = callback

    async def callback(self, interaction: discord.Interaction) -> Union[None, Any]:
        """Can be overridden
        """
        callback = self._callback
        return await callback(interaction) if callback else None
