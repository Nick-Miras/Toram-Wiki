from abc import ABC

from scraper.spiders.parsers.abc import ParserLeaf
from scraper.spiders.parsers.container_paths import MobPath


class MobParserLeaf(ParserLeaf, ABC):
    """Just to group the similar classes"""
    container_path = MobPath
