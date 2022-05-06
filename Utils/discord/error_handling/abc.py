import typing
from abc import ABC, abstractmethod
from typing import final

import discord
from discord.ext import commands


class OnError(ABC):

    def __init__(
            self,
            bot: commands.Bot,
            origin: discord.Message | discord.Interaction,
            exception: discord.DiscordException
    ):
        self.bot = bot
        self.origin = origin
        self.exception = exception

    async def get_context(self) -> commands.Context:
        return await self.bot.get_context(self.origin)

    @final
    async def get_handler(self) -> typing.Awaitable:
        return self.handler(await self.get_context(), self.exception)

    @staticmethod
    @abstractmethod
    async def handler(ctx: commands.Context, exception: discord.DiscordException) -> None:
        pass


IGNORED = (commands.CommandNotFound,)
