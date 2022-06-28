import discord
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group(invoke_without_command=True)
    async def help(self, ctx: commands.Context):
        pfx = ctx.prefix
        # main fields
        __fields = {
            f'{pfx}item': 'Command for searching information about Toram Items',
            f'{pfx}level': 'Command for searching the most optimal monster for obtaining experience',
            f'{pfx}monster': 'Command for searching information about Toram Monsters',
        }
        __admin_fields = {
            f'{pfx}set prefix': 'Sets the prefix'
        }

        if ctx.author.guild_permissions.administrator:
            __fields.update(__admin_fields)

        embed = discord.Embed()
        embed.set_author(name='Help')
        for name, value in __fields.items():
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
