from discord.ext import commands
import discord


class Help(commands.Cog):  # TODO: Create Paginator for each command

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group(invoke_without_command=True)
    async def help(self, ctx: commands.Context):
        pfx = ctx.prefix
        # main fields
        __fields = {
            f'{pfx}search': 'Command for searching information about Toram Items',
        }
        __admin_fields = {
            f'{pfx}set prefix': 'Sets the prefix'
        }

        if ctx.author.guild_permissions.administrator:
            __fields.update(__admin_fields)

        embed = discord.Embed()  # TODO: Improve Help Embed
        embed.set_author(name='Help')
        for name, value in __fields.items():
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
