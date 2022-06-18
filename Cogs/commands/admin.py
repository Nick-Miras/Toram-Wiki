import discord
from discord.ext import commands

from Cogs.exceptions import CmdError
from Utils.generics.embeds import SuccessEmbed
from database import get_mongodb_client
from database.models import WhiskeyDatabase


class Setters(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, name='set')
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        pfx = ctx.prefix
        __fields = {
            f'{pfx}set prefix': 'Sets the prefix'
        }
        embed = discord.Embed()
        embed.set_author(name='Set')
        for name, value in __fields.items():
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, prefix=None):
        if prefix is None:
            raise CmdError(f'`{ctx.prefix}set prefix [prefix]`')

        discord_guild = WhiskeyDatabase(get_mongodb_client()).discord_guilds
        discord_guild.update_one({'_id': ctx.guild.id}, {'$set': {'prefix': prefix}})
        await ctx.send(embed=SuccessEmbed.get(f'Set prefix to: `{prefix}`'))


async def setup(bot):
    await bot.add_cog(Setters(bot))
