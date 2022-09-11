import re
from abc import ABC, abstractmethod
from typing import Optional, Generator

from pydantic import HttpUrl

from Utils.dataclasses.abc import ItemType, get_item_type
from Utils.dataclasses.item import MarketValueDict, MaterialsDict, RecipeDict, LocationDict, UsesDict, StatsDict, \
    get_requirement_type, RequirementTypeSequence
from Utils.generics import arrays
from Utils.generics.numbers import try_int, extract_integer_from, convert_to_type_if_not_none
from Utils.generics.xpath import normalize_space, substring_before, extract_string_from_node
from Utils.types import StringOrInt, IdStringPair, OptionalStr, OptionalInt, SelectorType
from scraper.spiders.parsers.abc import ParserLeaf, CompositeParser, return_parser_results
from scraper.spiders.parsers.container_paths import ItemPath
from scraper.spiders.parsers.generics import get_container_from, is_container_null
from scraper.spiders.parsers.models import ParserResults


class ItemParserLeaf(ParserLeaf, ABC):
    """Just to group the similar classes"""
    container_path = ItemPath


class MarketValueParser(ItemParserLeaf):
    name = 'market value'

    @staticmethod
    @get_container_from(normalize_space('.//p[text()="Sell"]/following-sibling::p/text()'))
    def get_sell_value(container: SelectorType) -> OptionalInt:
        return extract_integer_from(container.get())

    @staticmethod
    @get_container_from(normalize_space('.//p[text()="Process"]/following-sibling::p/text()'))
    def get_process_value(container: SelectorType) -> OptionalStr:
        if process_value := container.get():
            return process_value

    @staticmethod
    @get_container_from(normalize_space('.//p[text()="Duration"]/following-sibling::p/text()'))
    def get_duration_time(container: SelectorType) -> OptionalStr:
        if duration_time := container.get():
            return duration_time

    @classmethod
    @return_parser_results(MarketValueDict)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        # not optional since everything can be processed or sold
        market_value_container = container.xpath(
            './/div[@class="item-prop mini"][./div/p[text()="Sell" or text()="Process" or text()="Duration"]]'
        )
        return {
            'sell': cls.get_sell_value(market_value_container),
            'process': cls.get_process_value(market_value_container),
            'duration': cls.get_duration_time(market_value_container)
        }


class AppearanceLinkParser(ItemParserLeaf):

    name = 'image'

    @classmethod
    @return_parser_results(HttpUrl)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        cond, app_container = is_container_null(container, './/div[@class="app-div"]')
        if cond is True:
            return
        partial_link = app_container.css('td').xpath('@background').get()
        return f"https://coryn.club/{partial_link.replace(' ', '%20')}"


class LocationParser(ItemParserLeaf):
    name = 'location'

    @staticmethod
    @get_container_from('.//div[@class="dye-group"]')
    def get_dye(container: SelectorType) -> Optional[tuple[StringOrInt, StringOrInt, StringOrInt]]:
        return tuple(map(try_int, container.xpath('./*/text()').getall()))

    @staticmethod
    def get_id_string_pair(container: SelectorType) -> IdStringPair:
        display_string: str = extract_string_from_node(container)
        try:
            return extract_integer_from(container.xpath('./a/@href').get()), display_string
        except (ValueError, TypeError):
            return None, display_string

    @classmethod
    def generate_locations(cls, container: SelectorType) -> Generator[LocationDict, None, None]:
        for sub_container in container:
            yield {
                'monster': cls.get_id_string_pair(sub_container.xpath('./div[1]')),
                'dye': cls.get_dye(sub_container),
                'map': cls.get_id_string_pair(sub_container.xpath('./div[3]'))
            }

    @classmethod
    @return_parser_results(list[LocationDict])
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        cond, location_containers = is_container_null(container, './/div[@class="pagination-js-item"]')
        if cond is True:
            return
        return list(cls.generate_locations(location_containers))


class GetMaterials(ABC):

    @staticmethod
    def get_material_amount(container: SelectorType) -> int:
        return extract_integer_from(container.xpath('./text()').get())

    @staticmethod
    @abstractmethod
    def get_material_string(container: SelectorType) -> IdStringPair:
        pass


class GetItemMaterial(GetMaterials):

    @staticmethod
    def get_material_string(container: SelectorType) -> IdStringPair:
        id_link: int = extract_integer_from(container.xpath('./a/@href').get())
        item_string: str = container.xpath('./a/text()').get()
        return id_link, item_string


class GetRawMaterial(GetMaterials):

    @staticmethod
    def get_material_string(container: SelectorType) -> IdStringPair:
        return None, container.xpath('substring-after(./text(), "x ")').get()


class RecipeParser(ItemParserLeaf):
    name = 'recipe'

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Materials"]]/div/ul/li')
    def get_materials(container: SelectorType) -> list[MaterialsDict]:
        def extract_materials():
            for material in container:
                if material.xpath('./a/text()').get():
                    strategy = GetItemMaterial
                    yield {
                        'amount': strategy.get_material_amount(material),
                        'item': strategy.get_material_string(material)
                    }
                else:
                    strategy = GetRawMaterial
                    yield {
                        'amount': strategy.get_material_amount(material),
                        'item': strategy.get_material_string(material)
                    }

        return list(extract_materials())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Fee"]]/div/text()')
    def get_fee(container: SelectorType) -> OptionalInt:
        return extract_integer_from(container.get())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Set"]]/div/text()')
    def get_set_pieces(container: SelectorType) -> int:
        return extract_integer_from(container.get())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Level"]]/div/text()')
    def get_level_requirement(container: SelectorType) -> OptionalInt:
        return extract_integer_from(container.get())

    @staticmethod
    @get_container_from('.//div[./p[@class="accent-bold"][text()="Difficulty"]]/div/text()')
    def get_crafting_difficulty(container: SelectorType) -> int:
        return extract_integer_from(container.get())

    @classmethod
    @return_parser_results(RecipeDict)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
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
    def uses_dict_builder(use_type: str, items: list[IdStringPair]) -> UsesDict:
        return {'type': use_type, 'items': items}

    @staticmethod
    @get_container_from('./p[@class="card-title"]/text()')
    def get_uses_type(container: SelectorType) -> Generator[str, None, None]:
        yield from container.getall()

    @staticmethod
    def get_uses_items_using(index: int, container: SelectorType) -> Generator[IdStringPair, None, None]:
        for item in container.xpath(f'./ul[count(preceding-sibling::p)={index}]'):
            id_: int = extract_integer_from(item.xpath('./li/a/@href').get())
            display_string: str = extract_string_from_node(item.xpath('./li'))
            yield id_, display_string

    @classmethod
    def generate_uses(cls, container: SelectorType) -> Generator[UsesDict, None, None]:
        for index, uses_type_str in enumerate(cls.get_uses_type(container), start=1):
            if uses_type_str == 'Upgrade Into':
                continue
            yield cls.uses_dict_builder(
                use_type=uses_type_str,
                items=list(cls.get_uses_items_using(index, container))
            )

    @classmethod
    @return_parser_results(list[UsesDict])
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
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
            id_link: int = extract_integer_from(crysta.xpath('./li/a/@href').get())
            item_name: str = crysta.xpath(normalize_space('./li/a/text()')).get()
            yield id_link, item_name

    @classmethod
    @return_parser_results(list[IdStringPair])
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
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
            id_link: int = extract_integer_from(crysta.xpath('@href').get())
            item_name: str = crysta.xpath(normalize_space('text()')).get()
            yield id_link, item_name

    @classmethod
    @return_parser_results(list[IdStringPair])
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        cond, container = is_container_null(container, './/div[@class="table-grid item-basestat"]')
        if cond is True or (return_val := cls.get_crystas(container)) is None:
            return
        return list(return_val)


class GetStats(ABC):

    @staticmethod
    @abstractmethod
    def fetch_key(container: SelectorType) -> str:
        pass

    @staticmethod
    @get_container_from(normalize_space('./div[2]/text()'))
    def fetch_value(container: SelectorType) -> float:
        return float(container.get())

    @classmethod
    def get_stat_attr_pair(cls, container: SelectorType) -> Optional[tuple[str, float]]:
        """
        Returns:
            A pair of stat and attribute pair
        """
        try:
            return cls.fetch_key(container), cls.fetch_value(container)
        except ValueError:
            return


class GetStatsWithoutRequirements(GetStats):

    @staticmethod
    @get_container_from(normalize_space('./div[1]/text()'))
    def fetch_key(container: SelectorType) -> str:
        return container.get()


class GetStatsWithRequirements(GetStats):

    @staticmethod
    @get_container_from(normalize_space('./div/div[@class="ml-10"]/text()'))
    def fetch_key(container: SelectorType) -> str:
        return container.get()


class StatsParser(ItemParserLeaf):
    name = 'stats'

    @staticmethod
    @get_container_from(substring_before(normalize_space('./div/b[@class="text-light"]/text()'), ' only:'))
    def get_weapon_requirement(container: SelectorType) -> Optional[RequirementTypeSequence]:
        if not (requirement := container.get()):
            return
        return get_requirement_type(requirement)

    @classmethod
    def has_weapon_requirement(cls, container: SelectorType) -> tuple[bool, RequirementTypeSequence]:
        weapon_requirement = cls.get_weapon_requirement(container)
        return bool(weapon_requirement), weapon_requirement

    @staticmethod
    def select_get_stat_strategy(weapon_requirement: Optional[RequirementTypeSequence], container: SelectorType) \
            -> Optional[tuple[Optional[RequirementTypeSequence], tuple[str, float]]]:
        match weapon_requirement:
            case None:
                if (stat_attr_pair := GetStatsWithoutRequirements.get_stat_attr_pair(container)) is None:
                    return
                return weapon_requirement, stat_attr_pair
            case _:
                if (stat_attr_pair := GetStatsWithRequirements.get_stat_attr_pair(container)) is None:
                    return
                return weapon_requirement, stat_attr_pair

    @classmethod
    def fetch_attributes(cls, container: SelectorType) -> \
            Generator[Optional[tuple[Optional[RequirementTypeSequence], tuple[str, float]]], None, None]:
        current_weapon_requirement: Optional[RequirementTypeSequence] = None
        for container in container.xpath('./div[position()>1]'):  # exclude first div: "Stat/Effect"
            cond, weapon_requirement = cls.has_weapon_requirement(container)
            if cond is True:
                current_weapon_requirement = weapon_requirement

            if (result := cls.select_get_stat_strategy(current_weapon_requirement, container)) is None:
                continue
            yield result

    @classmethod
    def generate_stats_dict(cls, container: SelectorType) -> Generator[StatsDict, None, None]:
        requirement_attribute_pair = list(cls.fetch_attributes(container))
        requirements: list[RequirementTypeSequence] = [
            convert_to_type_if_not_none(element, list)
            for element in
            arrays.remove_duplicates(
                convert_to_type_if_not_none(element[0], tuple) for element in requirement_attribute_pair
            )
        ]
        for requirement in requirements:
            attributes = []
            for req, attribute in requirement_attribute_pair:
                if requirement == req:
                    attributes.append(attribute)
            yield StatsDict(requirement=requirement, attributes=attributes)

    @classmethod
    @return_parser_results(list[StatsDict])
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        cond, container = is_container_null(container, './/div[text() = "Stat/Effect"]/following-sibling::div')
        if cond is True:
            return
        return list(cls.generate_stats_dict(container))


class IdParser(ItemParserLeaf):
    name = '_id'

    @staticmethod
    @get_container_from('.//div[./div[text()="Obtained From"]]/following-sibling::div/@id')
    def extract_id(container: SelectorType) -> int:
        return extract_integer_from(container.get())

    @classmethod
    @return_parser_results(int)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.extract_id(container)


class ItemTypeParser(ItemParserLeaf):
    name = 'type'

    @staticmethod
    @get_container_from('.//div[@class="card-title"]')
    def get_title(container: SelectorType) -> str:
        title: str = extract_string_from_node(container)
        return re.sub(r'.*\[(.*)].*', r'\1', title)

    @classmethod
    @return_parser_results(ItemType)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return get_item_type(cls.get_title(container))


class ItemNameParser(ItemParserLeaf):
    name = 'name'

    @staticmethod
    @get_container_from('.//div[@class="card-title"]')
    def get_title(container: SelectorType) -> str:
        title: str = extract_string_from_node(container)
        return re.sub(r'\s+\[.*]', '', title)

    @classmethod
    @return_parser_results(str)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_title(container)


class ItemCompositeParser(CompositeParser):
    container_path = ItemPath
    parsers: list[ParserLeaf] = [
        IdParser,
        ItemNameParser,
        ItemTypeParser,
        MarketValueParser,
        AppearanceLinkParser,
        LocationParser,
        RecipeParser,
        ItemUsesParser,
        UpgradesIntoParser,
        UpgradesFromParser,
        StatsParser
    ]
    parser_leaf_class = ItemParserLeaf


class UpgradesCompositeParser(ItemCompositeParser):
    parsers: list[ParserLeaf] = [UpgradesIntoParser, UpgradesFromParser]
