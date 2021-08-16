from Utils import PaginationItem, PaginatorView, PageSource, Paginator, SelectOption, global_dict, Dropdown
from discord.ext import commands
import discord
from typing import Any


class Source(PageSource):
    async def format_page(self, menu: Paginator, data: list[PaginationItem]):
        embed = discord.Embed()
        for item in data:
            embed.add_field(name=item.name, value='\u200b', inline=False)
        return embed


class Item(PaginationItem):
    async def display(self) -> Any:
        return self.name


class CustomDropdown(Dropdown):
    async def display(self) -> Any:
        paginator = self.paginator
        child: PaginationItem = paginator[self.values[0]]
        return await child.display()


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name='test')
    async def raw_test(self, ctx: commands.Context):
        def options(paginator: Paginator) -> list[SelectOption]:
            options = [SelectOption(label=item.name) for item in paginator.source.get_page(paginator.current_page)]
            return options

        text = [i for i in range(10)]
        data = [Item(name=item) for item in text]
        paginator = Paginator(source=Source(data, per_page=3))
        kwargs = await paginator.show_initial_page()
        await ctx.send(**kwargs, view=PaginatorView(ctx, paginator=paginator, dropdown=CustomDropdown))


def setup(bot):
    bot.add_cog(Test(bot))
