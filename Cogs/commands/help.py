import discord
from discord.ext import commands

from Utils.constants import images
from Utils.paginator.page import PageDataNode, MessageContentDisplay, D, ButtonItemsDisplay


class HelpRootNode(PageDataNode):

    def initialize(self) -> None:
        pass


class HelpRootNodeDisplayMessageContent(MessageContentDisplay):

    def get_data(self) -> D:
        pass


class HelpRootNodeButtonsItemDisplay(ButtonItemsDisplay):

    def get_data(self) -> D:
        pass


class HelpPageNode(PageDataNode):

    def initialize(self) -> None:
        pass


class HelpPageNodeDisplayMessageContent(MessageContentDisplay):

    def get_data(self) -> D:
        pass


class HelpPageNodeButtonsItemDisplay(ButtonItemsDisplay):

    def get_data(self) -> D:
        pass


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group(invoke_without_command=True)
    async def help(self, ctx: commands.Context):
        pfx = ctx.prefix
        # main fields
        __fields = {
            f'{pfx}item': 'Command for Searching Information About Toram Items',
            f'{pfx}level': 'Command for Searching the Most Optimal Monster for Obtaining Experience',
            f'{pfx}monster': 'Command for Searching Information About Toram Monsters',
            f'{pfx}partners': 'Our Partners!',
        }
        __admin_fields = {
            f'{pfx}set prefix': 'Sets the prefix',
        }

        if ctx.author.guild_permissions.administrator:
            __fields.update(__admin_fields)

        embed = discord.Embed(
            colour=discord.Colour.blurple(),
        )
        embed.set_author(name='Help')
        embed.set_thumbnail(url=images.SCROLL2)
        for name, value in __fields.items():
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
