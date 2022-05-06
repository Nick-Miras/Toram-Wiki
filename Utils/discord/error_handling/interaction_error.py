import discord
from discord.ext import commands

from Utils.discord.error_handling.abc import OnError, IGNORED
from Utils.discord.error_handling.handler import get_matching_error, DiscordError


class OnInteractionError(OnError):
    @staticmethod
    async def handler(ctx: commands.Context, exception: discord.DiscordException) -> None:
        if ctx.interaction.command.on_error is not None:
            # This prevents any commands with local handlers being handled here
            return

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        exception = getattr(exception, 'original', exception)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(exception, IGNORED):
            return

        if (discord_error := get_matching_error(ctx, exception)) is not None:  # type: DiscordError
            await discord_error.throw(ctx, exception)
