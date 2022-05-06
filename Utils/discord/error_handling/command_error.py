import discord
from discord.ext import commands

from Utils.discord.error_handling.abc import OnError, IGNORED
from Utils.discord.error_handling.handler import get_matching_error, DiscordError


class OnCommandError(OnError):
    @staticmethod
    async def handler(ctx: commands.Context, exception: discord.DiscordException) -> None:
        if hasattr(ctx.command, 'on_error'):
            # This prevents any commands with local handlers being handled here
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog

        if cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        exception = getattr(exception, 'original', exception)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(exception, IGNORED):
            return

        if (discord_error := get_matching_error(ctx, exception)) is not None:  # type: DiscordError
            await discord_error.throw(ctx, exception)
