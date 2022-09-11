from abc import ABC
from typing import Optional, Generator

from Utils.dataclasses.abc import Difficulty, Element, ItemType, DyeType
from Utils.dataclasses.monster import MonsterDrop
from Utils.generics.numbers import try_int
from Utils.generics.strings import convert_to_bool, strip_enclosing_brackets, strip_enclosing_parentheses
from Utils.generics.xpath import normalize_space, substring_after
from Utils.types import SelectorType, IdStringPair
from scraper.spiders.parsers.abc import ParserLeaf, return_parser_results, CompositeParser
from scraper.spiders.parsers.container_paths import MonsterPath
from scraper.spiders.parsers.generics import get_container_from
from scraper.spiders.parsers.models import ParserResults


class MonsterParserLeaf(ParserLeaf, ABC):
    """Just to group the similar classes"""
    container_path = MonsterPath


class MonsterNameParser(MonsterParserLeaf):
    """Parser for the Monster Name"""
    name = 'name'

    @staticmethod
    @get_container_from(normalize_space('.//div[@class="card-title-inverse"]/text()'))
    def get_monster_name(container: SelectorType) -> str:
        return container.get()

    @classmethod
    @return_parser_results(str)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_name(container)


class MonsterLevelParser(MonsterParserLeaf):
    """Parser for the Monster Level"""
    name = 'level'

    @staticmethod
    @get_container_from('.//div[@class="item-prop col-2"]/div/p[text()="Lv"]/following-sibling::p/text()')
    def get_monster_level(container: SelectorType) -> int:
        return int(container.get())

    @classmethod
    @return_parser_results(int)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_level(container)


class MonsterDifficultyParser(MonsterParserLeaf):
    """Parser for the Monster Difficulty"""
    name = 'difficulty'

    @staticmethod
    @get_container_from('.//div[@class="item-prop col-2"]/div/p[text()="Type"]/following-sibling::p/text()')
    def get_monster_difficulty(container: SelectorType) -> Optional[Difficulty]:
        try:
            difficulty = Difficulty(strip_enclosing_parentheses(container.get()).capitalize())
        except ValueError:
            return
        else:
            return difficulty

    @classmethod
    @return_parser_results(Difficulty)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_difficulty(container)


class MonsterHPParser(MonsterParserLeaf):
    """Parser for the Monster HP"""
    name = 'hp'

    @staticmethod
    @get_container_from('.//div[@class="item-prop col-2"]/div/p[text()="HP"]/following-sibling::p/text()')
    def get_monster_hp(container: SelectorType) -> int:
        return int(container.get())

    @classmethod
    @return_parser_results(int)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_hp(container)


class MonsterElementParser(MonsterParserLeaf):
    """Parser for the Monster Element"""
    name = 'element'

    @staticmethod
    @get_container_from('.//div[@class="item-prop col-2"]/div/p[text()="Element"]/following-sibling::p/text()')
    def get_monster_element(container: SelectorType) -> Optional[Element]:
        try:
            element = Element(container.get())
        except ValueError:
            return
        else:
            return element

    @classmethod
    @return_parser_results(Element)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_element(container)


class MonsterExpParser(MonsterParserLeaf):
    """Parser for the Monster EXP"""
    name = 'exp'

    @staticmethod
    @get_container_from('.//div[@class="item-prop col-2"]/div/p[text()="Exp"]/following-sibling::p/text()')
    def get_monster_exp(container: SelectorType) -> int:
        return int(container.get())

    @classmethod
    @return_parser_results(int)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_exp(container)


class MonsterTamableStatusParser(MonsterParserLeaf):
    """Parser for the Monster Tamable Status"""
    name = 'tamable'

    @staticmethod
    @get_container_from('.//div[@class="item-prop col-2"]/div/p[text()="Tamable"]/following-sibling::p/text()')
    def get_monster_tamable_status(container: SelectorType) -> bool:
        return convert_to_bool(container.get())

    @classmethod
    @return_parser_results(bool)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_tamable_status(container)


class MonsterImageParser(MonsterParserLeaf):
    """Parser for the Monster Image"""
    name = 'image'

    @staticmethod
    @get_container_from('.//div[@class="item-prop col-2"]/preceding-sibling::div/img/@src')
    def get_monster_image(container: SelectorType) -> Optional[str]:
        if partial_link := container.get():
            return f"https://coryn.club/{partial_link.replace(' ', '%20')}"

    @classmethod
    @return_parser_results(str)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_image(container)


class MonsterLocationParser(MonsterParserLeaf):
    """Parser for the Monster Location"""
    name = 'location'

    @staticmethod
    @get_container_from('.//div[@class="accent-bold" and text()="Spawn at"]/following-sibling::div/a')
    def get_monster_location(container: SelectorType) -> Optional[IdStringPair]:
        if location := container:
            map_id = int(location.xpath(substring_after('./@href', 'map.php?id=')).get())
            map_name = location.xpath('./text()').get()
            return map_id, map_name

    @classmethod
    @return_parser_results(IdStringPair)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_location(container)


class MonsterDropsParser(MonsterParserLeaf):
    """Parser for the Monster Drop"""
    name = 'drops'

    @staticmethod
    @get_container_from('./div/descendant-or-self::*/text()')
    def get_item_type(container: SelectorType) -> ItemType:
        return ItemType(strip_enclosing_brackets(container.get().strip()))

    @staticmethod
    @get_container_from('./div/a')
    def get_drop_information(container) -> IdStringPair:
        return int(container.xpath(substring_after('./@href', 'item.php?id=')).get()), container.xpath('./text()').get()

    @staticmethod
    @get_container_from('./div[@class="dye-group"]')
    def get_dye_tuple(container) -> Optional[DyeType]:
        if container.get():
            return tuple(map(try_int, container.xpath('./*/text()').getall()))

    @classmethod
    def generate_monster_drops(cls, container: SelectorType) -> Generator[MonsterDrop, None, None]:
        for drop in container.xpath('./div[@class="monster-drop pagination-js-item"]'):
            yield MonsterDrop(
                type=cls.get_item_type(drop),
                name=cls.get_drop_information(drop),
                dye=cls.get_dye_tuple(drop)
            )

    @classmethod
    @return_parser_results(list[MonsterDrop])
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return list(
            cls.generate_monster_drops(container.xpath('.//div[@class="pagination-js-items monster-drop-list"]')))


class MonsterIdParser(MonsterParserLeaf):
    """Parser for the Monster ID"""
    name = '_id'

    @staticmethod
    @get_container_from(substring_after('.//div[@class="js-pagination"]/@id', 'monster-drop-'))
    def get_monster_id(container: SelectorType) -> Optional[int]:
        if monster_id := container.get():
            return int(monster_id)

    @classmethod
    @return_parser_results(int)
    def get_result(cls, container: SelectorType, response) -> list[ParserResults]:
        return cls.get_monster_id(container)


class MonsterCompositeParser(CompositeParser):
    container_path = MonsterPath
    parsers = [
        MonsterNameParser,
        MonsterLevelParser,
        MonsterDifficultyParser,
        MonsterExpParser,
        MonsterHPParser,
        MonsterElementParser,
        MonsterTamableStatusParser,
        MonsterImageParser,
        MonsterIdParser,
        MonsterLocationParser,
        MonsterDropsParser
    ]
    parser_leaf_class = MonsterParserLeaf
