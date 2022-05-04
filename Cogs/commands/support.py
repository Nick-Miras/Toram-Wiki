from textwrap import dedent
from typing import Optional

import discord
from discord.ext import commands

from Cogs.exceptions import CmdError


class SupportCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    async def report(self, ctx: commands.Context, *, message: Optional[str] = None):
        # TODO: Add custom message cooldown
        if message is None:
            raise CmdError(f'`{ctx.prefix}report (message)')
        if message_length := len(message) > 1000:
            message = dedent(f"""\
            Message cannot be more than 1000 characters!
            You exceeded by `{message_length - 1000}` characters.
            """)
            raise CmdError(message, embed=True)

        bot_owner: discord.User = await self.bot.fetch_user(await self.bot.owner_id)
        channel: discord.DMChannel = await bot_owner.create_dm()
        embed = discord.Embed(description=message)
        embed.set_author(name='Bug Report')  # TODO: Add Setting Thumbnail
        await channel.send(embed=embed)

