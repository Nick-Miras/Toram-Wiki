import itertools
import re
from textwrap import dedent
from typing import Any, Optional, Generator

import discord
from discord.ext import commands

from Utils import PaginationItem, PaginatorView, PageSource, Paginator, SelectOption, Dropdown, ItemNotFound
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
        item = DisplayItem(self.item)
        return await item.display_as_embed()


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


class TruncateString:
    pass


class DisplayItem:
    def __init__(self, item: Item):
        self.item = item

    @staticmethod
    def __clean_string(string: str, sep='\n', limit: int = 1024) -> tuple:
        if len(string) > limit:
            strings = string.split(sep)
            lengths = [len(location) for location in strings]  # list[int]
            exceeded_amount = len(string) - 1024
            __cumulative_length = 0
            i = 1
            for i, length in enumerate(reversed(lengths), start=1):
                __cumulative_length += length
                if __cumulative_length >= exceeded_amount:
                    break

            # returns the first i string then returns the last i strings
            return sep.join(strings[:-i]), sep.join(strings[-i:])

        return string, None

    @classmethod
    def truncate_string(cls, string: str, sep='\n', limit=1024) -> Generator[str, None, None]:
        """truncates a string at a certain limit with certain separators

        Returns truncated string
        """
        truncated_str, extra_str = cls.__clean_string(string, sep, limit=limit)
        yield truncated_str
        while extra_str:  # while there is an extra string
            truncated_str, extra_str = cls.__clean_string(extra_str, sep, limit=limit)
            yield truncated_str

    @classmethod
    def _truncator(cls, strings: iter):  # combines strings by the `sep` variable then truncates them
        sep = '\n\n'
        for string in cls.truncate_string(sep.join(strings), sep):
            yield string

    @staticmethod
    def apply_image_to(embed: discord.Embed, item: Item):
        if not (image := item.image):
            return

        embed.set_thumbnail(url=image)

    @staticmethod
    def apply_market_value_to(embed: discord.Embed, item: Item):
        if not (market_value := item.market_value):
            return

        for key, value in market_value.items():
            embed.add_field(name=key.capitalize(), value=value, inline=False)

    @staticmethod
    def apply_stats_to(embed: discord.Embed, item: Item):
        def get_stats(stats: dict):
            for tree, stat_list in stats.items():
                if tree != 'main':
                    yield f'**{tree} only:**'
                for stat in stat_list:  # type: dict
                    string = f'{stat["attr"]} **{stat["value"]}**'
                    yield string if tree == 'main' else f' {string}'  # else indent it

        if not (stats := item.stats):  # type: dict
            return

        value = '\n'.join(get_stats(stats))
        embed.add_field(name='Stats:', value=value, inline=False)

    @staticmethod
    def apply_note_to(embed: discord.Embed, item: Item):
        if not (note := item.note):
            return

        embed.add_field(name='Description:', value=note, inline=False)

    @classmethod
    def apply_locations_to(cls, embed: discord.Embed, item: Item):
        def get_locations_from(locations: list[dict]) -> Generator[str, None, None]:
            for location in locations:
                string = []
                for key, value in location.items():
                    if not value:
                        continue
                    string.append(f'**{key.capitalize()}**: {value}')
                yield '\n'.join(string)

        if not (locations := item.location):  # type: list[dict]
            return

        for location in cls._truncator(get_locations_from(locations)):
            embed.add_field(name='Location:', value=location, inline=False)

    @classmethod
    def apply_uses_to(cls, embed: discord.Embed, item: Item):
        def get_uses_from(uses: list[dict]) -> Generator[str, None, None]:
            for use in uses:
                attr = use['attr'].capitalize()
                value = '\n'.join(use['value'])
                for group_of_strings in cls.truncate_string(value):
                    # truncates then groups the strings of `value` just in case it surpasses 1024 characters
                    yield f'**{attr}**:\n{group_of_strings}'

        if not (uses := item.uses):  # type: list[dict]
            return

        for uses in cls._truncator(get_uses_from(uses)):
            embed.add_field(name='Uses:', value=uses, inline=False)

    @staticmethod
    def apply_recipe_to(embed: discord.Embed, item: Item):
        def get_recipes_from(recipe: dict) -> Generator[str, None, None]:
            for key, value in recipe.items():
                if isinstance(value, dict):  # this only occurs once we get to the required materials part
                    def get_materials_from(materials: dict) -> Generator[str, None, None]:
                        for material_name, amount in materials.items():  # TODO: Maybe truncate this???
                            yield f'- {amount}x {material_name}'
                    value = '\n'.join(get_materials_from(value))
                yield f'**{key.capitalize()}**:\n{value}'

        if not (recipe := item.recipe):  # type: dict
            return

        embed.add_field(name='Recipe:', value='\n'.join(get_recipes_from(recipe)), inline=False)

    @classmethod
    def apply_embed_fields_to(cls, embed: discord.Embed, item: Item):  # maybe create coroutine
        pair = embed, item

        # TODO: Decide whether to make these into decorators
        cls.apply_image_to(*pair)
        cls.apply_market_value_to(*pair)
        cls.apply_stats_to(*pair)
        cls.apply_note_to(*pair)
        cls.apply_locations_to(*pair)
        cls.apply_uses_to(*pair)
        cls.apply_recipe_to(*pair)

    @staticmethod
    def embed_format(item: Item):
        embed = discord.Embed(
            colour=0xffd700
        )

        embed.set_author(name=item.names['display'], icon_url=Images.scroll)
        embed.set_footer(text='Credits: coryn.club')

        return embed

    async def get_embed_pages(self) -> Generator[discord.Embed, None, None]:
        def grouper(group_size, iterable):
            args = [iter(iterable)] * group_size
            return itertools.zip_longest(*args)

        item = self.item
        embed = self.embed_format(item)

        _temp_embed = discord.Embed()  # temporary embed used for applying the fields
        self.apply_embed_fields_to(_temp_embed, item)  # adds all the corresponding fields

        fields = _temp_embed._fields
        for page_number, grouped_fields in enumerate(grouper(10, fields), start=1):
            new_embed = embed.copy()
            embed.set_footer(text=f'Credits: coryn.club | Page: {page_number}')
            new_embed._fields = list(filter(lambda element: element is not None, grouped_fields))
            yield new_embed

    async def display_as_embed(self) -> discord.Embed:
        item = self.item
        embed = self.embed_format(item)

        self.apply_embed_fields_to(embed, item)  # adds all the corresponding fields

        # TODO: PAGINATE IF NO. OF FIELDS ARE MORE THAN 10
        return embed


class ItemQueryFactory:
    def __init__(self, query: str):
        self.query = query

    @staticmethod
    def _process_results(results: list[dict]) -> list[Item]:
        """Turns a list of result documents into a list of `class`:Item
        """
        def mapper(item: dict):
            return Item.from_dict(item)

        return list(map(mapper, results))

    @staticmethod
    def _process_items(items: list[Item]) -> list[ItemPagination]:
        """Turns a list of `class`:`Item` into a list of Items to be Paginated
        """
        def mapper(item: Item):
            return ItemPagination(name=item.names['display'], item=item)

        return list(map(mapper, items))

    @staticmethod
    async def display_item_as_embed(item: Item) -> dict[str, discord.Embed]:
        item = DisplayItem(item)
        embed = await item.display_as_embed()
        return {'embed': embed}

    @classmethod
    async def create_paginator_view_from_items(cls, ctx: commands.Context, items: list[Item]) -> dict[str, Any]:
        data: list[ItemPagination] = cls._process_items(items)

        # creates the paginator class
        paginator = Paginator(source=Source(data, per_page=5))

        # creates the View Class that is composed py the Paginator Class
        view = PaginatorView(ctx, paginator=paginator, dropdown=QueryDropdown)

        message_kwargs = await paginator.show_initial_page()
        return {**message_kwargs, 'view': view}

    @staticmethod
    async def fetch_results(query: str) -> list[dict]:
        """returns a list of database documents
        """
        query_item = QueryItem(query)
        try:
            results: list[dict] = await query_item.output()
        except ItemNotFound:
            embed = Models.error_embed('Item Not Found!')
            raise Error(embed, embed=True)
        else:
            return results

    async def get_message_data(self, ctx: commands.Context) -> dict:
        """returns a dictionary that can be used as discord.Message data.
        """
        results: list[dict] = await self.fetch_results(self.query)

        # should I use walrus here for the sake of walruses?
        if len(items := self._process_results(results)) == 1:  # type: list[Item]
            return await self.display_item_as_embed(items[0])
        else:
            return await self.create_paginator_view_from_items(ctx, items)


class Query(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    async def item(self, ctx, *, query: Optional[str] = None):
        if query is None:
            raise Error(f'`{ctx.prefix}item (item name)`')

        search_for_this = ItemQueryFactory(query=query)
        message_data: dict = await search_for_this.get_message_data(ctx)
        await ctx.send(**message_data)

    @commands.command()
    async def search(self, ctx):
        error_message = dedent(f"""\
        Deprecated!
        Use `{ctx.prefix}item` instead!
        Note: Boss Search is not yet added
        """)
        raise Error(error_message, embed=True)


def setup(bot):
    bot.add_cog(Query(bot))
