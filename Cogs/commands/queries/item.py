import textwrap
from abc import ABC, abstractmethod
from typing import TypeVar, Optional, Generator
from uuid import UUID

import discord
from discord import Interaction, SelectOption
from discord import app_commands
from discord.ext import commands

from Cogs.exceptions import CmdError
from Utils.constants import images, colors
from Utils.dataclasses.item import ItemComposite, ItemLeaf
from Utils.generics import split_by_max_character_limit, arrays
from Utils.generics.discord import to_message_data, send_with_paginator
from Utils.paginator.buttons import GoLeft, GoRight, GoFirst, GoLast, BetterSelectContainer, SelectContainerData, GoBack
from Utils.paginator.page import PageDataNode, PageDataNodePromise, PageDataTree, ContentDisplay, ItemsDisplay, \
    TreeInformation, DisplayData, PageTreeController, PaginatorView
from database import get_mongodb_client
from database.command.read import TriGramSearch
from database.models import WhiskeyDatabase, QueryInformation

D = TypeVar('D')


class IDisplayItemLeaf(ABC):

    def __init__(self, leaf: ItemLeaf):
        self.item = leaf

    @abstractmethod
    def set_market_value(self, embed: discord.Embed) -> None:
        pass

    @abstractmethod
    def set_image(self, embed: discord.Embed) -> None:
        pass

    @abstractmethod
    def set_stats(self, embed: discord.Embed) -> None:
        pass

    @abstractmethod
    def set_location(self, embed: discord.Embed) -> None:
        pass

    @abstractmethod
    def set_recipe(self, embed: discord.Embed) -> None:
        pass

    @abstractmethod
    def set_uses(self, embed: discord.Embed) -> None:
        pass

    @abstractmethod
    def set_upgrades(self, embed: discord.Embed) -> None:
        pass

    def get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            colour=0xffd700
        )

        embed.set_author(name=self.item.name, icon_url=images.SCROLL)
        embed.set_footer(text='Credits: coryn.club')
        if self.item.image:
            self.set_image(embed)
        if self.item.market_value:
            self.set_market_value(embed)
        if self.item.stats:
            self.set_stats(embed)
        if self.item.upgrades:
            self.set_upgrades(embed)
        if self.item.location:
            self.set_location(embed)
        if self.item.recipe:
            self.set_recipe(embed)
        if self.item.uses:
            self.set_uses(embed)
        return embed


class DisplayItemLeaf(IDisplayItemLeaf):

    def set_market_value(self, embed: discord.Embed) -> None:
        for key, value in dict(self.item.market_value).items():
            embed.add_field(name=key.capitalize(), value=value, inline=False)

    def set_image(self, embed: discord.Embed) -> None:
        embed.set_thumbnail(url=self.item.image)

    def set_stats(self, embed: discord.Embed) -> None:
        def generate_stats():
            for stat in self.item.stats:
                if (requirement := stat.requirement) is not None:
                    requirement_string = f'{", ".join(requirement)} only:'
                    yield requirement_string
                for name, value in stat.attributes:
                    yield f'{name} **{value}**'

        for index, string_group in enumerate(split_by_max_character_limit(list(generate_stats()))):
            if index == 0:
                embed.add_field(name='Stats:', value='\n'.join(string_group), inline=False)
            else:
                embed.add_field(name='\u200b', value='\n'.join(string_group), inline=False)

    def set_location(self, embed: discord.Embed) -> None:
        def get_location() -> Generator[str, None, None]:
            for location in self.item.location:
                def get_location_group() -> Generator[str, None, None]:
                    if monster := location.monster:
                        yield f'**Monster**: {monster[1] if monster else ""}'
                    if dye := location.dye:
                        yield f'**Dye**: {dye}'
                    if map_ := location.map:
                        yield f'**Map**: {map_[1] if map_ else ""}'
                    yield '\n'
                yield '\n'.join(get_location_group())

        for string_group in split_by_max_character_limit(list(get_location())):  # type: list[str]
            embed.add_field(name='Location:', value=''.join(string_group), inline=False)

    def set_recipe(self, embed: discord.Embed) -> None:
        recipe = self.item.recipe

        def get_recipe():
            yield textwrap.dedent(f"""\
            Fee: {recipe.fee}
            Set: {recipe.set}
            Level: {recipe.level}
            Difficulty: {recipe.difficulty}
            Materials:""")
            for material in recipe.materials:
                yield textwrap.indent(f'x{material.amount} - {material.item[1]}', '\t')

        for index, string_group in enumerate(split_by_max_character_limit(list(get_recipe()))):
            if index == 0:
                embed.add_field(name='Recipe:', value='\n'.join(string_group), inline=False)
            else:
                embed.add_field(name='\u200b', value='\n'.join(string_group), inline=False)

    def set_uses(self, embed: discord.Embed) -> None:
        def get_uses():
            for uses_dict in self.item.uses:
                yield f'**{uses_dict.type}**:'
                for item in uses_dict.items:
                    yield item[1]

        for index, string_group in enumerate(split_by_max_character_limit(list(get_uses()))):
            if index == 0:
                embed.add_field(name='Uses:', value='\n'.join(string_group), inline=False)
            else:
                embed.add_field(name='\u200b', value='\n'.join(string_group), inline=False)

    def set_upgrades(self, embed: discord.Embed) -> None:
        upgrades_into = self.item.upgrades.upgrades_into
        upgrades_into_string = ", ".join(id_string_pair[1] for id_string_pair in upgrades_into) if upgrades_into else ''
        upgrades_from = self.item.upgrades.upgrades_from
        upgrades_from_string = ", ".join(id_string_pair[1] for id_string_pair in upgrades_from) if upgrades_from else ''
        if not upgrades_from_string and not upgrades_into_string:
            return
        embed.add_field(
            name='Upgrades',
            value=f'Into: {upgrades_into_string}\nFrom: {upgrades_from_string}',
            inline=False
        )


class ItemRootPageNode(PageDataNode):
    """used as placeholder for paginated root"""

    def initialize(self) -> None:
        return


class ItemRootPaginatedNode(PageDataNodePromise):
    """displays the name of the composites"""

    def initialize(self) -> None:
        return

    @staticmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        """
        Args:
            child: :class:`ItemCompositePageNode`
        Returns:
            :class:`ItemCompositePageNode`
        """
        child_data: ItemComposite = child.data
        items_leaf = WhiskeyDatabase(get_mongodb_client()).items_leaf
        for leaf in child_data.leaves:
            leaf_data = ItemLeaf.parse_obj(items_leaf.find_one({'_id': leaf.item_composite_leaf_id}))
            leaf_name = f'{leaf_data.name} [{leaf.difference}] {"[Dye]" if leaf.has_dye is True else ""}'
            child.add_child(ItemLeafPagePromiseNode(
                controller=child.controller,
                information=TreeInformation(name=leaf_name),
                data=leaf_data,
                display_data=DisplayData(items=ItemLeafItemDisplay, content=ItemLeafDisplayContent)
            ))
        return child


class ItemCompositePageNode(PageDataNodePromise[ItemComposite]):
    """displays the name of the leaves"""

    def initialize(self) -> None:
        return

    @staticmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        """
        Args:
            child: :class:`ItemLeafPagePromiseNode`
        Returns:
            :class:`ItemLeafPagePromiseNode`
        """
        return child


class ItemLeafPagePromiseNode(PageDataNodePromise[ItemLeaf]):

    def initialize(self) -> None:
        return

    @staticmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        return child


class ItemDropdown(BetterSelectContainer):

    async def callback(self, interaction: Interaction):
        child_id, = self.values  # type: str
        self.controller.goto_child(UUID(child_id))


class ItemRootDisplayContent(ContentDisplay):
    def get_data(self) -> D:
        return


class ItemRootItemDisplay(ItemsDisplay):
    def get_data(self) -> D:
        return


class ItemRootPaginatedDisplayContent(ContentDisplay):
    def get_data(self) -> D:
        siblings = self.tree.parent.children
        current_page = siblings.index(self.tree)
        offset = (current_page * 5) + 1
        children: list[PageDataTree] = self.tree.children
        children_as_string: list[str] = [
            f'> **{index}. {child.name}**' for index, child in enumerate(children, start=offset)
        ]
        embed = discord.Embed(
            colour=colors.BRIGHT_GREEN,
            description='\n'.join(children_as_string)
        )
        embed.set_author(name='Results')
        embed.set_thumbnail(url=images.MONOCLE)
        embed.set_footer(text=f'Page {current_page + 1}/{len(siblings)}')
        return to_message_data(embed)


class ItemRootPaginatedItemDisplay(ItemsDisplay):

    def get_data(self) -> D:
        siblings = self.tree.parent.children
        sibling_number = len(siblings)
        current_page = siblings.index(self.tree)
        offset = (current_page * 5) + 1
        controller = self.tree.controller
        children: list[PageDataTree] = self.tree.children
        select_options = [
            SelectOption(label=f'{index}. {child.name}', value=str(child.id))
            for index, child in enumerate(children, start=offset)
        ]
        select_container_data = SelectContainerData(placeholder='More Information...', options=select_options)
        dropdown = ItemDropdown(controller=controller, data=select_container_data)
        if sibling_number == 2:
            return [GoLeft(controller), GoRight(controller), dropdown]
        if sibling_number > 2:
            return [GoFirst(controller), GoLeft(controller), GoRight(controller), GoLast(controller), dropdown]
        return [dropdown]


class ItemCompositeDisplayContent(ContentDisplay):
    def get_data(self) -> D:
        children: list[PageDataTree] = self.tree.children
        children_as_string: list[str] = [
            f'> **{index}. {child.name}**' for index, child in enumerate(children, start=1)
        ]
        embed = discord.Embed(
            colour=colors.BRIGHT_GREEN,
            description='\n'.join(children_as_string)
        )
        embed.set_author(name=self.tree.name)
        embed.set_thumbnail(url=images.MONOCLE)
        return to_message_data(embed)


class ItemCompositeItemDisplay(ItemsDisplay):
    def get_data(self) -> D:
        controller = self.tree.controller
        children: list[PageDataTree] = self.tree.children
        select_options = [
            SelectOption(label=f'{index}. {child.name.title()}', value=str(child.id))
            for index, child in enumerate(children, start=1)
        ]
        select_container_data = SelectContainerData(placeholder='More Information...', options=select_options)
        dropdown = ItemDropdown(controller=controller, data=select_container_data)
        return [GoBack(controller), dropdown]


class ItemLeafDisplayContent(ContentDisplay):
    def get_data(self) -> D:
        return to_message_data(DisplayItemLeaf(self.tree.data).get_embed())


class ItemLeafItemDisplay(ItemsDisplay):
    def get_data(self) -> D:
        return [GoBack(self.tree.controller)]


def query_item(query: str) -> Optional[list[dict]]:
    items_composite = WhiskeyDatabase(get_mongodb_client()).items_composite
    matches: list[dict] = list(
        TriGramSearch().query(QueryInformation(collection=items_composite, to_search=query), limit=25)
    )
    if len(matches) > 0:
        return matches


async def client(ctx: commands.Context, query_string: str):
    if (matches := query_item(query_string)) is None:
        raise CmdError('Item Not Found!', should_use_embed=True)

    controller = PageTreeController()
    page_item_composite = [
        ItemCompositePageNode(
            controller=controller,
            information=TreeInformation(name=item_composite.name),
            display_data=DisplayData(
                items=ItemCompositeItemDisplay,
                content=ItemCompositeDisplayContent
            ),
            data=item_composite
        ) for item_composite in (ItemComposite.parse_obj(match) for match in matches)
    ]
    page_item_composite_paginated = [
        ItemRootPaginatedNode(
            controller=controller,
            information=TreeInformation(),
            display_data=DisplayData(
                items=ItemRootPaginatedItemDisplay,
                content=ItemRootPaginatedDisplayContent
            ),
            children=item_composite_chunk
        ) for item_composite_chunk in arrays.split_by_chunk(page_item_composite, 5)
    ]
    ItemRootPageNode(controller=controller, information=TreeInformation(), children=page_item_composite_paginated)
    controller.current = page_item_composite_paginated[0]
    view = PaginatorView(ctx, controller)
    controller.view = view
    await send_with_paginator(ctx, view)


class ItemQueryCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='item')
    async def item_normal_command(self, ctx: commands.Context, *, query: Optional[str] = None):
        if query is None:
            raise CmdError(f'> {ctx.prefix}{ctx.invoked_with} (item: word)')
        await client(ctx, query)

    @app_commands.command(name='item')
    @app_commands.describe(query='The item to search for')
    @app_commands.checks.bot_has_permissions(send_messages=True)
    async def item_app_command(self, interaction: Interaction, query: str):
        await interaction.response.defer()
        await client(await self.bot.get_context(interaction), query)

    # @item_app_command.autocomplete('query')
    # async def item_autocomplete(self, interation: Interaction, current: str) -> list[app_commands.Choice[str]]:
    #     items_composite = WhiskeyDatabase(get_mongodb_client()).items_composite
    #     raw_results: list[dict] = list(
    #         EdgeGramSearch().query(QueryInformation(collection=items_composite, to_search=current), limit=5)
    #     )[0:5]
    #     return [app_commands.Choice(name=match, value=match) for match in (result['name'] for result in raw_results)]


async def setup(bot: commands.Bot):
    await bot.add_cog(ItemQueryCommands(bot))
