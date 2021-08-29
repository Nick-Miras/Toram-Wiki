import re
from typing import Any, Optional

import discord
from discord.ext import commands

from Utils import PaginationItem, PaginatorView, PageSource, Paginator, SelectOption, Dropdown
from Utils.errors import Error
from Utils.variables import Images, Models
from Utils.wiki import QueryItem, Item


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
        source = paginator.source
        offset = paginator.current_page * source.per_page
        options = [SelectOption(label=f'{num}. {item.name}') for num, item in
                   enumerate(source.get_page(paginator.current_page), start=offset + 1)]
        return options

    async def display(self) -> Any:
        paginator = self.paginator
        item_name = re.sub(r'\d+\.\s', '', self.values[0])
        item: ItemPagination = paginator[item_name]
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
        if stats := item.stats:  # TODO: Decide whether to Indent
            _string = ''
            for key, value in stats.items():
                _string += f'{key} **{value}**\n'
            embed.add_field(name='Stats:', value=_string, inline=False)
        if note := item.note:
            embed.add_field(name="Description:", value=note, inline=False)
        if location := item.location:
            embed.add_field(name="Location:", value=location, inline=False)
        embed.set_footer(text='Credits: coryn.club')

        return embed

    @staticmethod
    def _process_results(results: list[dict]) -> list[Item]:
        def mapper(item: dict):
            return Item.from_dict(item)

        return list(map(mapper, results))

    @staticmethod
    def _process_items(items: list[Item]) -> list[ItemPagination]:
        def mapper(item: Item):
            return ItemPagination(item.name, item)

        return list(map(mapper, items))

    @classmethod
    async def _search(cls, ctx: commands.Context, query: str) -> dict:
        query_item = QueryItem(query)
        results: list[dict] = await query_item.output()

        if not results:
            embed = Models.error_embed('Item Not Found!')
            raise Error(embed, embed=True)

        if len(items := cls._process_results(results)) == 1:  # type: list[Item]
            embed = await cls.display_as_embed(items[0])
            return {'embed': embed}
        else:
            data: list[ItemPagination] = cls._process_items(items)
            paginator = Paginator(source=Source(data, per_page=5))
            view = PaginatorView(ctx, paginator=paginator, dropdown=QueryDropdown)
            kwargs = await paginator.show_initial_page()
            return {**kwargs, 'view': view}

    @commands.command()
    async def search(self, ctx, *, query: Optional[str] = None):
        if query is None:
            raise Error(f'`{ctx.prefix}search (item name)`')

        kwargs = await self._search(ctx, query)
        await ctx.send(**kwargs)


def setup(bot):
    bot.add_cog(Query(bot))
