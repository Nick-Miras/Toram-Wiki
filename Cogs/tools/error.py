import sys
import traceback

import discord
from discord.ext import commands

from Utils import exceptions
from Utils.constants import Models
from Utils.generics.embeds import ErrorEmbed


class Error(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            print("local overwritten")
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                print("overwritten")
                return

        ignored = (commands.CommandNotFound,)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        # Main
        # TODO: Consider whether using ELIF Statements
        if isinstance(error, commands.RoleNotFound):
            arg = error.argument
            await ctx.send(f'{arg} is an invalid role')
            return

        if isinstance(error, commands.MemberNotFound):
            error = ErrorEmbed.get(f'Could not find `{error.argument}`!')
            await ctx.send(embed=error)

        if isinstance(error, commands.BadArgument):
            await ctx.send("> Invalid Arguments")

        if isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]

            if len(missing) > 2:
                fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            message = 'Bot requires {} permission(s) to run this command.'.format(fmt)
            await ctx.send(f"> {message}")

        if isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]

            if len(missing) > 2:
                fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            message = 'You are missing {} permission(s) to run this command.'.format(fmt)
            await ctx.send(f"> {message}")

        if isinstance(error, commands.NotOwner):
            await ctx.send("> You do not have the permissions...")

        if isinstance(error, commands.UserNotFound):
            await ctx.send("> User not Found...")

        if isinstance(error, errors.Error):
            message = error.message
            if isinstance(message, str):
                if error.use_embed:  # If true then use the error_embed
                    embed = ErrorEmbed.get(message)
                    args = {'embed': embed, 'content': None}
                else:
                    args = {'content': message, 'embed': None}
            if isinstance(message, discord.Embed):
                args = {'embed': message, 'content': None}

            if error.channel:
                await error.channel.send(**args)
            else:
                try:
                    await ctx.reply(**args)
                except discord.HTTPException:
                    await ctx.send(**args)
            raise error  # Raise Error

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(Error(bot))
