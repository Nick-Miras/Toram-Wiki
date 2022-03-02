import discord
from discord.ext import commands

from Utils.database import Database
from Utils.exceptions import Error
from Utils.constants import Models
from Utils.generics.embeds import SuccessEmbed


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
        embed = discord.Embed()  # TODO: Improve Help Embed
        embed.set_author(name='Set')
        for name, value in __fields.items():
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @settings.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, prefix=None):
        if prefix is None:
            raise Error(f'`{ctx.prefix}set prefix [prefix]`')

        Database.GUILDS.update_one({'_id': ctx.guild.id}, {'$set': {'prefix': prefix}})
        await ctx.send(embed=SuccessEmbed.get(f'Set prefix to: `{prefix}`'))


def setup(bot):
    bot.add_cog(Setters(bot))
