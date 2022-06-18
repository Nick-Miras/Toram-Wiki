import re
from abc import ABC
from typing import Optional, Generator

from Utils.dataclasses.levelling import ExpData
from Utils.generics.numbers import extract_integer_from, get_float_from, try_int, to_ordinal
from Utils.generics.xpath import normalize_space
from Utils.types import IdStringPair, SelectorType, OptionalStr
from scraper.spiders.parsers.abc import ParserLeaf, CompositeParser, return_parser_results
from scraper.spiders.parsers.container_paths import LevellingPath
from scraper.spiders.parsers.generics import get_container_from
from scraper.spiders.parsers.models import ParserResults


class LevellingParserLeaf(ParserLeaf, ABC):
    """Just to group the similar classes"""
    container_path = LevellingPath


class MobType(LevellingParserLeaf):
    name = 'mob type'

    @classmethod
    @return_parser_results(str)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        return container.xpath(normalize_space('./../preceding-sibling::div/h3[last()]/text()')).get()


class MobLevel(LevellingParserLeaf):
    name = 'mob level'

    @classmethod
    @return_parser_results(int)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        return extract_integer_from(container.xpath('./div[@class="level-col-1"]/b').get())


class MobInformation(LevellingParserLeaf):
    name = 'mob information'

    @staticmethod
    @get_container_from('@href')
    def get_id(container: SelectorType) -> int:
        return extract_integer_from(container.get())

    @staticmethod
    @get_container_from('text()')
    def get_display_string(container: SelectorType) -> str:
        return container.get()

    @classmethod
    @return_parser_results(IdStringPair)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        container = container.xpath('./div[@class="level-col-2"]/p/b/a')
        return cls.get_id(container), cls.get_display_string(container)


class MobLocation(LevellingParserLeaf):
    name = 'mob location'

    @classmethod
    @return_parser_results(str)
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        return container.xpath('./div[@class="level-col-2"]/p[2]/text()').get()


class ExpInformation(LevellingParserLeaf):
    name = 'exp information'
    
    @staticmethod
    @get_container_from('./b/text()')
    def get_exp(container: SelectorType) -> int:
        return extract_integer_from(container.get())

    @staticmethod
    @get_container_from('./text()')
    def get_not_bold_exp(container: SelectorType) -> int:
        """
        Use an entirely different xpath for extracting the exp,
        because Coryn places the exp information differently for not-bolded exp string.
        """
        return extract_integer_from(container.get())

    @staticmethod
    @get_container_from('./i/text()')
    def get_break_status(container: SelectorType) -> OptionalStr:
        if try_int(break_status := re.sub(r'.*\((.*)\sbreak\)', r'\1', container.get())) == 0:
            return
        return to_ordinal(int(break_status)) if break_status.isnumeric() else break_status

    @staticmethod
    @get_container_from('./small/text()')
    def get_exp_progress(container: SelectorType) -> float:
        return get_float_from(container.get())

    @classmethod
    def generate_exp_data(cls, container: SelectorType) -> Generator[ExpData, None, None]:
        for container in container.xpath('./p'):
            exp = cls.get_exp(container) or cls.get_not_bold_exp(container)
            break_status = cls.get_break_status(container)
            exp_progress = cls.get_exp_progress(container)
            yield {'exp': exp, 'break status': break_status, 'exp progress': exp_progress}

    @classmethod
    @return_parser_results(list[ExpData])
    def get_result(cls, container: SelectorType) -> list[ParserResults]:
        container = container.xpath('./div[@class="level-col-3"]')
        return list(cls.generate_exp_data(container))


class LevellingCompositeParser(CompositeParser):
    container_path = LevellingPath
    parsers: list[ParserLeaf] = [
        MobType,
        MobLevel,
        MobInformation,
        MobLocation,
        ExpInformation
    ]

    @staticmethod
    def parser_validator(parser: ParserLeaf) -> tuple[bool, Optional[str]]:
        if isinstance(parser, LevellingParserLeaf.__class__) is False:
            return False, f'Expected {LevellingParserLeaf} not {parser.__class__}'
        return True, None
