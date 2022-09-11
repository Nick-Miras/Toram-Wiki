from abc import ABC

from lxml.html import fromstring
from scrapy.http import Response

from Utils.types import SelectorType
from scraper.spiders.parsers.abc import ParserLeaf, return_parser_results, CompositeParser
from scraper.spiders.parsers.container_paths import SkillPath
from scraper.spiders.parsers.generics import get_container_from
from scraper.spiders.parsers.models import ParserResults


class SkillParserLeaf(ParserLeaf, ABC):
    """Just to group the similar classes"""
    container_path = SkillPath


class SkillDetailsParser(SkillParserLeaf):
    """Parser for the Skill Details"""
    name = 'details'

    @staticmethod
    @get_container_from('.//details/span[@class="sub-title"]/following-sibling::*')
    def get_skill_details(container: SelectorType) -> str:
        for form in container:
            form_id = form.xpath('@id').get()
            full_page = container.xpath('/').get()
            form_page = fromstring(full_page)
            continue
        return ''

    @classmethod
    @return_parser_results(str)
    def get_result(cls, container: SelectorType, response: Response) -> list[ParserResults]:
        for form in container.xpath('.//details/span[@class="sub-title"]/following-sibling::*'):
            form_id = form.xpath('@id').get()
            form_page = fromstring(response.body)
            forms = form_page.forms
        return ' cls.get_skill_details(container)'


class SkillCompositeParser(CompositeParser):
    container_path = SkillPath
    parsers = [SkillDetailsParser]
    parser_leaf_class = SkillParserLeaf
