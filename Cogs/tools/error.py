import sys
import traceback
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic, Optional

import discord
from discord.ext import commands
from discord.ext.commands import Context

import Cogs.exceptions
from Utils.generics.embeds import ErrorEmbed

T = TypeVar('T')
IGNORED = (commands.CommandNotFound,)


class DiscordError(ABC, Generic[T]):

    @abstractmethod
    async def throw(self, ctx: Context, error: T):
        pass


class RoleNotFound(DiscordError[commands.RoleNotFound]):

    async def throw(self, ctx: Context, error: T):
        arg = error.argument
        await ctx.send(f'{arg} is an invalid role')


class MemberNotFound(DiscordError[commands.MemberNotFound]):

    async def throw(self, ctx: Context, error: T):
        error = ErrorEmbed.get(f'Could not find `{error.argument}`!')
        await ctx.send(embed=error)


class BadArgument(DiscordError[commands.BadArgument]):

    async def throw(self, ctx: Context, error: T):
        await ctx.send("> Invalid Arguments")


class MissingPermissions(DiscordError, ABC, Generic[T]):

    @staticmethod
    @abstractmethod
    def get_message(fmt) -> str:
        pass

    async def throw(self, ctx: Context, error: T):
        missing = [
            perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions
        ]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        await ctx.send(f"> {self.get_message(fmt)}")


class UserMissingPermissions(MissingPermissions[commands.MissingPermissions]):
    @staticmethod
    def get_message(fmt) -> str:
        return f"You are missing {fmt} permission(s) to run this command."


class BotMissingPermissions(MissingPermissions[commands.BotMissingPermissions]):

    @staticmethod
    def get_message(fmt) -> str:
        return f"Bot is missing {fmt} permission(s) to run this command."


class NotOwner(DiscordError[commands.NotOwner]):

    async def throw(self, ctx: Context, error: T):
        await ctx.send("> You do not have the permissions...")


class UserNotFound(DiscordError[commands.UserNotFound]):

    async def throw(self, ctx: Context, error: T):
        await ctx.send("> User not Found...")


class CustomCmdError(DiscordError[Cogs.exceptions.CmdError]):
    
    @staticmethod
    def get_message_content(error: T) -> dict[str, Any]:
        error: Cogs.exceptions.CmdError
        match error.message:
            case str():
                if error.should_use_embed is True:
                    return {'embed': ErrorEmbed.get(error.message), 'content': None}
                else:
                    return {'content': error.message, 'embed': None}
            case discord.Embed():
                return {'embed': error.message, 'content': None}
    
    async def throw(self, ctx: Context, error: T):
        message_content = self.get_message_content(error)

        if error.channel:
            await error.channel.send(**message_content)
        else:
            try:
                await ctx.reply(**message_content)
            except discord.HTTPException:
                await ctx.send(**message_content)
        raise error  # Raise Error


def get_matching_error(ctx, error: commands.CommandError) -> Optional[DiscordError]:
    match error:
        case commands.RoleNotFound():
            return RoleNotFound()
        case commands.MemberNotFound():
            return MemberNotFound()
        case commands.BadArgument():
            return BadArgument()
        case commands.BotMissingPermissions():
            return BotMissingPermissions()
        case commands.MissingPermissions():
            return MissingPermissions()
        case commands.NotOwner():
            return NotOwner()
        case commands.UserNotFound():
            return UserNotFound()
        case Cogs.exceptions.CmdError():
            return CustomCmdError()
        case _:
            if type(error) in IGNORED:
                return

            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


class Error(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            print("local overwritten")
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        
        if cog._get_overridden_method(cog.cog_command_error) is not None:
            print("overwritten")
            return

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, IGNORED):
            return

        if (discord_error := get_matching_error(ctx, error)) is not None:  # type: DiscordError
            await discord_error.throw(ctx, error)


async def setup(bot):
    await bot.add_cog(Error(bot))
