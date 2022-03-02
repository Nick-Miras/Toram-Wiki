from abc import ABC, abstractmethod
from typing import Optional, Union, Generator

from pydantic import HttpUrl

from Utils.dataclasses.item import MarketValueDict, MaterialsDict, RecipeDict, LocationDict, UsesDict
from Utils.generics.numbers import try_int, get_integer_from
from Utils.types import StringOrInt, IdStringPair, OptionalStr, OptionalInt, SelectorType
from .abc import ParserLeaf, CompositeParser, ParserResults, return_parser_results
from .container_paths import ItemPath
from .generics import get_container_from, is_container_null
from Utils.generics.xpath import normalize_space, get_non_empty_string


class ItemParserLeaf(ParserLeaf, ABC):
    """Just to group the similar classes"""
    container_path = ItemPath


class MarketValueParser(ItemParserLeaf):
    name = 'market value'

    @staticmethod
    @get_container_from('.//p[text()="Sell"]/following-sibling::p/text()')
    def get_sell_value(container: SelectorType) -> OptionalInt:
        return get_integer_from(container.get())

    @staticmethod
    @get_container_from('.//p[text()="Process"]/following-sibling::p/text()')
    def get_process_value(container: SelectorType) -> OptionalStr:
        return container.get()

    @classmethod
    @return_parser_results(MarketValueDict)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        # not optional since everything can be processed or sold
        market_value_container = container.xpath('.//div[@class="item-prop mini"]/div[.//p[@class="accent-bold"]]')
        return {
            'sell': cls.get_sell_value(market_value_container),
            'process': cls.get_process_value(market_value_container)
        }


class AppearanceLinkParser(ItemParserLeaf):

    name = 'appearance'

    @classmethod
    @return_parser_results(HttpUrl)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        if not (app_container := container.css('div.app-div')).get():
            return
        partial_link = app_container.css('td').xpath('@background').get()
        return f"https://coryn.club/{partial_link.replace(' ', '%20')}"


class LocationParser(ItemParserLeaf):
    name = 'location'

    @staticmethod
    @get_container_from('./div[1]')
    def get_monster(container: SelectorType) -> Union[IdStringPair, tuple[str, str]]:
        """
        Returns
        -------
        monster id and display string
        and never returns None
        """
        if (child := container.xpath('./font')).get():
            drop_type: str = child.xpath('./text()').get()  # should return [NPC] or [Player Skill]
            drop_source = container.xpath(get_non_empty_string('./text()')).get()
            return drop_type, drop_source

        id_link: str = container.xpath('./a/@href').get()
        monster_display_string: str = container.xpath(normalize_space('./a/text())')).get()
        return id_link, monster_display_string

    @staticmethod
    @get_container_from('.//div[@class="dye-group"]')
    def get_dye(container: SelectorType) -> Optional[tuple[StringOrInt, StringOrInt, StringOrInt]]:
        return tuple(map(try_int, container.xpath('./*/text()').getall()))

    @staticmethod
    @get_container_from('./div[3]')
    def get_map(container: SelectorType) -> Optional[Union[IdStringPair, tuple[None, str]]]:
        if map_string := container.xpath(normalize_space('./text()')).get():
            if map_string == 'Event':
                return None, 'Event'  # lack of information of event from coryn so return 'Event'
            return

        id_link: str = container.xpath('./a/@href').get()
        map_display_string: str = container.xpath(normalize_space('./a/text()')).get()
        return id_link, map_display_string

    @classmethod
    @return_parser_results(list[LocationDict])
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        cond, containers = is_container_null(container, './/div[@class="pagination-js-item"]')
        if cond is True:
            return

        def generate_locations() -> Generator[LocationDict, None, None]:
            for container in containers:
                yield {
                    'monster': cls.get_monster(container),
                    'dye': cls.get_dye(container),
                    'map': cls.get_map(container)
                }
        return list(generate_locations())


class GetMaterials(ABC):

    @staticmethod
    def get_material_amount(container: SelectorType) -> int:
        return get_integer_from(container.xpath('./text()').get())

    @staticmethod
    @abstractmethod
    def get_material_information(container: SelectorType):
        ...


class GetItemMaterial(GetMaterials):

    @staticmethod
    def get_material_information(container: SelectorType) -> IdStringPair:
        id_link: str = container.xpath('./a/@href').get()
        item_string: str = container.xpath('./a/text()').get()
        return id_link, item_string


class GetRawMaterial(GetMaterials):

    @staticmethod
    def get_material_information(container: SelectorType) -> tuple[None, str]:
        return None, container.xpath('substring-after(./text(), "x ")').get()


class RecipeParser(ItemParserLeaf):
    name = 'recipe'

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Materials"]]/div/ul/li')
    def get_materials(container: SelectorType) -> list[MaterialsDict]:
        def extract_materials():
            for material in container:
                if material.xpath('./a').get():
                    strategy = GetItemMaterial
                    yield {
                        'amount': strategy.get_material_amount(material),
                        'item': strategy.get_material_information(material)
                    }
                else:
                    strategy = GetRawMaterial
                    yield {
                        'amount': strategy.get_material_amount(material),
                        'item': strategy.get_material_information(material)
                    }

        return list(extract_materials())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Fee"]]/div/text()')
    def get_fee(container: SelectorType) -> OptionalInt:
        return get_integer_from(container.get())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Set"]]/div/text()')
    def get_set_pieces(container: SelectorType) -> int:
        return get_integer_from(container.get())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Level"]]/div/text()')
    def get_level_requirement(container: SelectorType) -> OptionalInt:
        return get_integer_from(container.get())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Difficulty"]]/div/text()')
    def get_crafting_difficulty(container: SelectorType) -> int:
        return get_integer_from(container.get())

    @classmethod
    @return_parser_results(RecipeDict)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        cond, container = is_container_null(container, './/div[text()="Recipe"]/../following-sibling::div')
        if cond is True:
            return
        return {
            'fee': cls.get_fee(container),
            'set': cls.get_set_pieces(container),
            'level': cls.get_level_requirement(container),
            'difficulty': cls.get_crafting_difficulty(container),
            'materials': cls.get_materials(container)
        }


class ItemUsesParser(ItemParserLeaf):
    name = 'uses'

    @staticmethod
    def uses_dict_builder(type: str, items: list[IdStringPair]) -> UsesDict:
        return {'type': type, 'items': items}

    @staticmethod
    @get_container_from('./p[@class="card-title"]/text()')
    def get_uses_type(container: SelectorType) -> Generator[str, None, None]:
        yield from container.getall()

    @staticmethod
    def get_uses_items_using(index: int, container: SelectorType) -> Generator[IdStringPair, None, None]:
        for item in container.xpath(f'./ul[count(preceding-sibling::p)={index}]'):
            id_link: str = item.xpath('./li/a/@href').get()
            item_name: str = item.xpath(normalize_space('./li/a/text()')).get()
            item_amount: str = item.xpath(get_non_empty_string('./li/text()')).get()
            display_string: str = item_name + " " + item_amount
            yield id_link, display_string

    @classmethod
    def generate_uses(cls, container: SelectorType) -> Generator[UsesDict, None, None]:
        for index, uses_type_str in enumerate(cls.get_uses_type(container), start=1):
            if uses_type_str == 'Upgrade Into':
                continue
            yield cls.uses_dict_builder(
                type=uses_type_str,
                items=list(cls.get_uses_items_using(index, container))
            )

    @classmethod
    @return_parser_results(list[UsesDict])
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        cond, container = is_container_null(container, './/div[./div[text() = "Used For"]]/following-sibling::div')
        if cond is True or len(return_val := list(cls.generate_uses(container))) == 0:
            return
        return return_val


class UpgradesItemParserLeaf(ItemParserLeaf, ABC):
    """Parser for Xtal Upgrades"""


class UpgradesIntoParser(ItemParserLeaf):
    name = 'upgrades into'

    @staticmethod
    @get_container_from('./p[text() = "Upgrade Into"]/following-sibling::ul')
    def get_crysta(container: SelectorType) -> Generator[IdStringPair, None, None]:
        for crysta in container:
            id_link: str = crysta.xpath('./li/a/@href').get()
            item_name: str = crysta.xpath(normalize_space('./li/a/text()')).get()
            yield id_link, item_name

    @classmethod
    @return_parser_results(list[IdStringPair])
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        cond, container = is_container_null(container, './/div[./div[text() = "Used For"]]/following-sibling::div')
        if cond is True or (return_val := cls.get_crysta(container)) is None:
            return
        return list(return_val)


class UpgradesFromParser(ItemParserLeaf):
    name = 'upgrades from'

    @staticmethod
    @get_container_from('./div[./div[normalize-space(text()) = "Upgrade for"]]/div[2]/a')
    def get_crystas(container: SelectorType) -> Generator[IdStringPair, None, None]:
        for crysta in container:
            id_link: str = crysta.xpath('@href').get()
            item_name: str = crysta.xpath(normalize_space('text()')).get()
            yield id_link, item_name

    @classmethod
    @return_parser_results(list[IdStringPair])
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        cond, container = is_container_null(container, './/div[@class="table-grid item-basestat"]')
        if cond is True or (return_val := cls.get_crystas(container)) is None:
            return
        return list(return_val)


class ItemCompositeParser(CompositeParser):
    container_path = ItemPath
    parsers: list[ParserLeaf] = [
        MarketValueParser,
        AppearanceLinkParser,
        LocationParser,
        RecipeParser,
        ItemUsesParser,
        UpgradesIntoParser,
        UpgradesFromParser
    ]

    @staticmethod
    def parser_validator(parser: ParserLeaf) -> tuple[bool, Optional[str]]:
        if isinstance(parser, ItemParserLeaf.__class__) is False:
            return False, f'Expected {ItemParserLeaf} not {parser.__class__}'
        return True, None


class UpgradesCompositeParser(ItemCompositeParser):
    parsers: list[ParserLeaf] = [UpgradesIntoParser, UpgradesFromParser]
