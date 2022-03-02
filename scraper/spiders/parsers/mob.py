from abc import ABC

from .abc import ParserLeaf
from .container_paths import MobPath


class MobParserLeaf(ParserLeaf, ABC):
    """Just to group the similar classes"""
    container_path = MobPath
