import inspect
from types import FunctionType

from Utils import PaginationItem, PaginatorView, PageSource, Paginator, SelectOption, global_dict, Dropdown
from discord.ext import commands
import discord
from discord.ui import Select
from typing import Any
import pickle


class Source(PageSource):
    async def format_page(self, data: list[PaginationItem]):
        embed = discord.Embed()
        for item in data:
            embed.add_field(name=item.name, value='\u200b', inline=False)
        return embed


class Item(PaginationItem):
    async def display(self) -> Any:
        return self.name


class CustomDropdown(Dropdown):
    pass


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name='test')
    async def raw_test(self, ctx: commands.Context):
        def options(paginator: Paginator) -> list[SelectOption]:
            """
            """
            options = [SelectOption(label=item.name) for item in paginator.source.get_page(paginator.current_page)]
            return options

        text = [i for i in range(10)]
        data = [Item(name=item) for item in text]
        paginator = Paginator(source=Source(data, per_page=3))
        await ctx.send('Test', view=PaginatorView(ctx, paginator=paginator, options=options, dropdown=CustomDropdown))


def setup(bot):
    bot.add_cog(Test(bot))
