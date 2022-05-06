from textwrap import dedent, indent
from typing import Optional, Generator, Generic, TypeVar

import discord
from discord import Interaction, SelectOption, app_commands
from discord.ext import commands
from discord.ext.commands import Context as Ctx
from scrapyscript import Job as ScrapyJob, Processor as ScrapyProcessor

from Cogs.exceptions import CmdError
from Utils.dataclasses.levelling import LevellingInformation, ExpData
from Utils.generics import arrays
from Utils.generics.discord import to_message_data, send_with_paginator
from Utils.generics.numbers import seperate_integer
from Utils.paginator.buttons import BetterSelectContainer, SelectContainerData, GoBackTwice
from Utils.paginator.buttons import GoLeft, GoRight, GoLast, GoFirst
from Utils.paginator.page.display import ContentDisplay, ItemsDisplay, DisplayData
from Utils.paginator.page.models import TreeInformation
from Utils.paginator.page.tree import PageDataTree, PageDataNode, PageDataNodePromise, PageTreeController
from Utils.paginator.page.view import PaginatorView
from scraper.spiders.converters import LevellingInformationConverter
from scraper.spiders.parsers.coryn.levelling import LevellingCompositeParser
from scraper.spiders.scrapers import ScraperInformation
from scraper.spiders.scrapers.concrete_scrapers import CorynScraper

D = TypeVar('D')


class LevellingPageNode(PageDataNode, Generic[D]):

    def initialize(self) -> None:
        return


class LevellingPagePromiseNode(PageDataNodePromise):

    def initialize(self) -> None:
        self.controller.current = self.children[0]

    @staticmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        """A method that generates the children of a PageDataNode and returns it"""
        return child  # TODO: Return Mob Information


class LevellingNodeDropdown(BetterSelectContainer):

    async def callback(self, interaction: Interaction):
        self.controller.goto_child(self.values[0])


class LevellingChildContent(ContentDisplay):

    def get_data(self) -> D:
        data = self.tree.data
        embed = discord.Embed(
            title=self.tree.parent.name.title()
        )
        for datum in data:  # type: LevellingInformation
            def exp_string_builder(exp_data: ExpData) -> str:
                exp, break_status, exp_progress = exp_data.values()
                return f'{seperate_integer(exp)} (Break: {break_status}) - {exp_progress}%'

            exp_earned = indent('\n'.join(exp_string_builder(info) for info in datum.exp_information), '  ')
            description = dedent(f"""\
            Monster Level: {datum.mob_level}
            Location: {datum.mob_location}
            Experience Earned:
            """)
            embed.add_field(name=datum.mob_information[1], value=f'```{description}{exp_earned}```', inline=False)
        return to_message_data(embed)


class LevellingChildItems(ItemsDisplay):

    def get_data(self) -> D:
        sibling_number = len(self.tree.parent.children)
        controller = self.tree.controller
        if sibling_number == 1:
            return [GoBackTwice(controller)]
        if sibling_number == 2:
            return [GoBackTwice(controller), GoLeft(controller), GoRight(controller)]
        if sibling_number > 2:
            return [GoBackTwice(controller), GoLeft(controller), GoRight(controller), GoFirst(controller),
                    GoLast(controller)]


class LevellingRootContent(ContentDisplay):

    def get_data(self) -> D:
        data_by_mob_type: dict[str, list[LevellingInformation]] = {
            mob_type: [
                page_node for page_node in [
                    child for child in [
                        root.children for root in self.tree.children if root.name == mob_type]
                ]
            ][0]
            for mob_type in set(child_of_root.name for child_of_root in self.tree.children)
        }

        embed = discord.Embed()
        for mob_type, mobs in data_by_mob_type.items():  # type: str, list[LevellingPageNode[list[LevellingInformation]]]
            mob_data: list[LevellingInformation] = arrays.flatten(node.data for node in [mob for mob in mobs])
            description = indent('\n'.join(
                levelling_information.mob_information[1] for levelling_information in mob_data), '- ')
            embed.add_field(name=mob_type.title(), value=f'Number of Mobs: {len(mob_data)}', inline=False)

        return to_message_data(embed)


class LevellingRootItems(ItemsDisplay):

    def get_data(self) -> D:
        select_options = [SelectOption(label=child.name.title(), value=child.name) for child in self.tree.children]
        select_container = SelectContainerData(placeholder='More Information...', options=select_options)
        return [LevellingNodeDropdown(self.tree.controller, select_container)]


def scrape(level: int) -> Generator[LevellingInformation, None, None]:
    scraper_information = ScraperInformation(
        url=f'https://coryn.club/leveling.php?lv={level}',
        parser=LevellingCompositeParser,
        next_page=False,
        converter=LevellingInformationConverter()
    )

    job = ScrapyJob(CorynScraper, scraper_information)
    processor = ScrapyProcessor(settings=None)
    for result in processor.run(job):
        yield result['result']


def sort_by_mob_hierachy(mob_information: LevellingPagePromiseNode):
    mob_type = mob_information.name.lower()
    if mob_type == 'boss':
        return 1
    if mob_type == 'mini boss':
        return 0
    if mob_type == 'normal monsters':
        return -1


async def client(ctx: Ctx, level: int):
    if len(scraped := list(scrape(level))) < 1:
        raise CmdError('Level Not Found!', should_use_embed=True)

    controller = PageTreeController()
    data_by_mob_type: dict[str, list[list[LevellingInformation]]] = {
        mob_type: arrays.split_by_chunk([datum for datum in scraped if datum.mob_type == mob_type], 5)
        for mob_type in set(datum.mob_type for datum in scraped)
    }

    def construct_children(data: list[LevellingInformation]) -> LevellingPageNode:
        return LevellingPageNode[list[list[LevellingInformation]]](
            controller=controller,
            information=TreeInformation(),
            display_data=DisplayData(items=LevellingChildItems, content=LevellingChildContent),
            data=data
        )

    page_mob_type: list[LevellingPagePromiseNode] = [LevellingPagePromiseNode(
        controller=controller, information=TreeInformation(name=mob_type),
        display_data=DisplayData(),
        children=[construct_children(datum) for datum in data]
    ) for mob_type, data in data_by_mob_type.items()]  # child of the root

    page_root = LevellingPageNode(
        controller=controller,
        information=TreeInformation(),
        display_data=DisplayData(items=LevellingRootItems, content=LevellingRootContent),
        children=sorted(page_mob_type, key=sort_by_mob_hierachy)
    )
    controller.current = page_root
    view = PaginatorView(ctx, controller)
    controller.view = view
    await send_with_paginator(ctx, view)


class LevellingQueryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=('levelling', 'level'))
    async def levelling_query_normal_command(self, ctx: Ctx, level: Optional[int] = None):
        if level is None:
            raise CmdError(f'> {ctx.prefix}{ctx.invoked_with} (level: number)')
        await client(ctx, level)

    @app_commands.command(name='level')
    async def levelling_query_app_command(self, interaction: discord.Interaction, level: int):
        await interaction.response.defer()
        await client(await self.bot.get_context(interaction), level)


async def setup(bot: commands.Bot):
    await bot.add_cog(LevellingQueryCommands(bot))
