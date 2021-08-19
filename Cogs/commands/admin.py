import discord
from discord.ext import commands

from Utils.database import Database
from Utils.errors import Error
from Utils.variables import Models


class Setters(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, name='set')
    @commands.has_permissions(administrator=True)
    async def __setting(self, ctx):
        pfx = ctx.prefix
        __fields = {
            f'{pfx}set prefix': 'Sets the prefix'
        }
        embed = discord.Embed()  # TODO: Improve Help Embed
        embed.set_author(name='Set')
        for name, value in __fields.items():
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @__setting.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, prefix=None):
        if prefix is None:
            raise Error(f'`{ctx.prefix}set prefix [prefix]`')

        Database.GUILDS.update_one({'_id': ctx.guild.id}, {'$set': {'prefix': prefix}})
        await ctx.send(embed=Models.success_embed(f'Set prefix to: `{prefix}`'))


def setup(bot):
    bot.add_cog(Setters(bot))
