from Utils import PaginationItem, PaginatorView, PageSource, Paginator, SelectOption, global_dict, Dropdown
from Utils.errors import Error
from discord.ext import commands
import discord
from typing import Any, Optional
from Utils.wiki import QueryItem, Item
from Utils.variables import Images, Models
from textwrap import dedent


class Source(PageSource):
    async def format_page(self, menu: Paginator, data: list[PaginationItem]):
        embed = discord.Embed(
            colour=0xfb607f
        )
        embed.set_author(name='Did you mean?')
        embed.set_thumbnail(url=Images.monocle)

        names = [item.name for item in data]
        offset = menu.current_page * self.per_page
        embed.description = '\n'.join(f'> **{num}. {name}**' for num, name in enumerate(names, start=offset + 1))
        if self.max_pages > 1:
            embed.set_footer(text=f'Page: {menu.current_page + 1}/{self.max_pages}')
        else:
            embed.set_footer(text=f'Last Page')
        return embed


class ItemPagination(PaginationItem):
    async def display(self) -> discord.Embed:
        return await Query.display_as_embed(self.item)


class QueryDropdown(Dropdown):
    @staticmethod
    def get_options(paginator) -> list[SelectOption]:
        # TODO: enumerate items with numbers
        labels = []
        options = [SelectOption(label=item.name) for item in paginator.source.get_page(paginator.current_page)]
        return options

    async def display(self) -> Any:
        paginator = self.paginator
        item: ItemPagination = paginator[self.values[0]]
        return await item.display()


class Query(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @staticmethod
    async def display_as_embed(item: Item) -> discord.Embed:
        embed = discord.Embed(
            colour=0xffd700
        )
        embed.set_author(name=item.name, icon_url=Images.scroll)
        if image := item.image:
            embed.set_thumbnail(url=image)
        if note := item.note:
            embed.add_field(name="Description:", value=note, inline=False)
        if location := item.location:
            embed.add_field(name="Location:", value=location, inline=False)
        embed.set_footer(text='Credits: coryn.club')

        return embed

    @staticmethod
    def _process_results(results: list[dict]) -> list[Item]:
        def mapper(item: dict):
            try:
                item.pop('rank')
            except KeyError:
                pass
            return Item.from_dict(item)

        return list(map(mapper, results))

    @staticmethod
    def _process_items(items: list[Item]) -> list[ItemPagination]:
        def mapper(item: Item):
            return ItemPagination(item.name, item)
        return list(map(mapper, items))

    @commands.command()
    async def search(self, ctx, *, query: Optional[str] = None):
        if query is None:
            raise Error(f'`{ctx.prefix}search (item name)`')

        query_item = QueryItem(query)
        results: list[dict] = await query_item.output()
        if not results:
            embed = Models.error_embed('Item Not Found!')
            raise Error(embed, embed=True)

        items: list[Item] = self._process_results(results)
        if len(items) == 1:
            embed = await self.display_as_embed(items[0])
            return await ctx.send(embed=embed)

        data: list[ItemPagination] = self._process_items(items)
        paginator = Paginator(source=Source(data, per_page=5))
        view = PaginatorView(ctx, paginator=paginator, dropdown=QueryDropdown)
        kwargs = await paginator.show_initial_page()
        await ctx.send(**kwargs, view=view)


def setup(bot):
    bot.add_cog(Query(bot))
