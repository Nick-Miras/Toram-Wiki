import textwrap
from typing import Optional, TypeVar, Generator
from uuid import UUID

import discord
from discord import app_commands, Interaction, SelectOption
from discord.ext import commands

from Cogs.exceptions import CmdError
from Utils.constants import colors, images
from Utils.dataclasses.monster import MonsterLeaf, MonsterComposite, MonsterDrop
from Utils.generics import arrays, split_by_max_character_limit
from Utils.generics.discord import to_message_data, send_with_paginator
from Utils.paginator.buttons import GoBack, BetterSelectContainer, SelectContainerData, GoLeft, GoRight, GoFirst, GoLast
from Utils.paginator.page import PageDataNode, PageDataNodePromise, PageDataTree, TreeInformation, DisplayData, \
    ButtonItemsDisplay, MessageContentDisplay, PageTreeController, PaginatorView
from database import get_mongodb_client
from database.command.read import TextSearch
from database.indexes import AggregationIndexes
from database.models import WhiskeyDatabase, QueryInformation

D = TypeVar('D')


class ItemDropdown(BetterSelectContainer):

    async def callback(self, interaction: Interaction):
        child_id, = self.values  # type: str
        self.controller.goto_child(UUID(child_id))


class MonsterPageRootNode(PageDataNode):
    """used as placeholder for paginated root"""

    def initialize(self) -> None:
        return


class MonsterRootDisplayMessageContent(MessageContentDisplay):
    def get_data(self) -> D:
        return


class MonsterRootItemDisplayButton(ButtonItemsDisplay):
    def get_data(self) -> D:
        return


class MonsterPaginatedRootNode(PageDataNodePromise):
    """displays the name of the composites"""

    def initialize(self) -> None:
        return

    @staticmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        child_data: MonsterComposite = child.data
        monsters_leaf_db_collection = WhiskeyDatabase(get_mongodb_client()).monsters_leaf
        for monster_leaf in child_data.leaves:
            monster_leaf_data = MonsterLeaf.parse_obj(
                monsters_leaf_db_collection.find_one({'_id': monster_leaf.monster_composite_leaf_id})
            )
            child.add_child(MonsterLeafPagePromiseNode(
                controller=child.controller,
                information=TreeInformation(name=monster_leaf_data.name),
                data=monster_leaf_data,
                display_data=DisplayData(items=ItemLeafItemDisplayButton, content=MonsterLeafDisplayMessageContent)
            ))
        return child


class MonsterRootPaginatedDisplayMessageContent(MessageContentDisplay):
    def get_data(self) -> D:
        siblings = self.tree.parent.children
        current_page = siblings.index(self.tree)
        offset = (current_page * 5) + 1
        children: list[PageDataTree] = self.tree.children
        children_as_string: list[str] = [
            f'> **{index}. {child.name}** [{child.data.location[1]}]' for index, child in
            enumerate(children, start=offset)
        ]
        embed = discord.Embed(
            colour=colors.BRIGHT_GREEN,
            description='\n'.join(children_as_string)
        )
        embed.set_author(name='Results')
        embed.set_thumbnail(url=images.MONOCLE)
        embed.set_footer(text=f'Page {current_page + 1}/{len(siblings)}')
        return to_message_data(embed)


class MonsterRootPaginatedItemDisplayButton(ButtonItemsDisplay):
    def get_data(self) -> D:
        siblings = self.tree.parent.children
        sibling_number = len(siblings)
        current_page = siblings.index(self.tree)
        offset = (current_page * 5) + 1
        controller = self.tree.controller
        children: list[PageDataTree] = self.tree.children
        select_options = [
            SelectOption(label=f'{index}. {child.name} [{child.data.location[1]}]', value=str(child.id))
            for index, child in enumerate(children, start=offset)
        ]
        select_container_data = SelectContainerData(placeholder='More Information...', options=select_options)
        dropdown = ItemDropdown(controller=controller, data=select_container_data)
        if sibling_number == 2:
            return [GoLeft(controller), GoRight(controller), dropdown]
        if sibling_number > 2:
            return [GoFirst(controller), GoLeft(controller), GoRight(controller), GoLast(controller), dropdown]
        return [dropdown]


class MonsterCompositePageNode(PageDataNodePromise[MonsterComposite]):
    """displays the name of the leaves"""

    def initialize(self) -> None:
        return

    @staticmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        return child


class MonsterCompositeDisplayMessageContent(MessageContentDisplay):
    def get_data(self) -> D:
        children: list[PageDataTree] = self.tree.children
        children_as_string: list[str] = [
            f'> **{index}. {child.name}** [{child.data.level}] [{child.data.difficulty}]'
            for index, child in enumerate(children, start=1)
        ]
        embed = discord.Embed(
            colour=colors.BRIGHT_GREEN,
            description='\n'.join(children_as_string)
        )
        embed.set_author(name=self.tree.name)
        embed.set_thumbnail(url=images.MONOCLE)
        return to_message_data(embed)


class MonsterCompositeItemDisplayButton(ButtonItemsDisplay):
    def get_data(self) -> D:
        controller = self.tree.controller
        children: list[PageDataTree] = self.tree.children
        select_options = [
            SelectOption(
                label=f'{index}. {child.name.title()} [{child.data.level}] [{child.data.difficulty}]',
                value=str(child.id)
            )
            for index, child in enumerate(children, start=1)
        ]
        select_container_data = SelectContainerData(placeholder='More Information...', options=select_options)
        dropdown = ItemDropdown(controller=controller, data=select_container_data)
        return [GoBack(controller), dropdown]


class MonsterLeafPagePromiseNode(PageDataNodePromise[MonsterLeaf]):

    def initialize(self) -> None:
        return

    @staticmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        return child


class MonsterLeafDisplayMessageContent(MessageContentDisplay):
    @staticmethod
    def get_drops(drops: list[MonsterDrop]) -> Generator[str, None, None]:
        for drop in drops:
            display_string = f"""\
            **Item**: {drop.name[1]}
            **Dye**: {drop.dye}
            
            """
            yield textwrap.dedent(display_string)

    def get_data(self) -> D:
        data: MonsterLeaf = self.tree.data
        embed = discord.Embed(
            colour=0xffd700
        )
        embed.set_author(name=data.name)
        embed.set_thumbnail(url='https://cdn.discordapp.com/emojis/853086959723741195.webp?size=4096&quality=lossless')
        for field in [
            ('Level', data.level),
            ('Difficulty', data.difficulty),
            ('HP', data.hp),
            ('Element', data.element),
            ('EXP', data.exp),
            ('Tamable', data.tamable),
            ('Location', data.location[1]),
        ]:
            embed.add_field(name=field[0], value=field[1], inline=True)
        if image := data.image:
            embed.set_image(url=image)
        for string_group in split_by_max_character_limit(list(self.get_drops(data.drops))):  # type: list[str]
            embed.add_field(name='Drops:', value=''.join(string_group), inline=False)
        embed.set_footer(text='Credits: coryn.club')

        return to_message_data(embed)


class ItemLeafItemDisplayButton(ButtonItemsDisplay):
    def get_data(self) -> D:
        return [GoBack(self.tree.controller)]


def query_monster(query: str) -> Optional[list[dict]]:
    monsters_composite_collection = WhiskeyDatabase(get_mongodb_client()).monsters_composite
    matches: list[dict] = list(
        TextSearch().query(
            QueryInformation(collection=monsters_composite_collection, to_search=query),
            AggregationIndexes.MonstersCompositeString,
            limit=25
        )
    )
    if len(matches) > 0:
        return matches


async def client(ctx: commands.Context, query_string: str):
    if (matches := query_monster(query_string)) is None:
        raise CmdError('Monster Not Found!', should_use_embed=True)

    controller = PageTreeController()
    monster_composite_node_lst = [
        MonsterCompositePageNode(
            controller=controller,
            information=TreeInformation(name=monster_composite.name),
            display_data=DisplayData(
                items=MonsterCompositeItemDisplayButton,
                content=MonsterCompositeDisplayMessageContent
            ),
            data=monster_composite
        ) for monster_composite in [MonsterComposite.parse_obj(match) for match in matches]
    ]
    paginated_root_nodes_lst = [
        MonsterPaginatedRootNode(
            controller=controller,
            information=TreeInformation(),
            display_data=DisplayData(
                items=MonsterRootPaginatedItemDisplayButton,
                content=MonsterRootPaginatedDisplayMessageContent
            ),
            children=monster_composite_node_lst_chunk
        ) for monster_composite_node_lst_chunk in arrays.split_by_chunk(monster_composite_node_lst, 5)

    ]
    MonsterPageRootNode(controller=controller, information=TreeInformation(), children=paginated_root_nodes_lst)
    controller.current = paginated_root_nodes_lst[0]
    view = PaginatorView(ctx, controller)
    controller.view = view
    await send_with_paginator(ctx, view)


class MonsterQueryCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='monster')
    async def monster_normal_command(self, ctx: commands.Context, *, query: Optional[str] = None):
        if query is None:
            raise CmdError(f'> {ctx.prefix}{ctx.invoked_with} (item: word)')
        await client(ctx, query)

    @app_commands.command(name='monster')
    @app_commands.describe(query='The monster to search for')
    @app_commands.checks.bot_has_permissions(send_messages=True)
    async def monster_app_command(self, interaction: Interaction, query: str):
        await interaction.response.defer()
        await client(await self.bot.get_context(interaction), query)


async def setup(bot: commands.Bot):
    await bot.add_cog(MonsterQueryCommands(bot))
