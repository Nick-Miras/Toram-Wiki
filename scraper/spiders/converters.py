from __future__ import annotations

from abc import ABC, abstractmethod
from typing import final

from Utils.dataclasses.abc import WikiBaseModel
from Utils.dataclasses.item import ItemLeaf
from Utils.dataclasses.levelling import LevellingInformation
from Utils.dataclasses.monster import MonsterLeaf
from scraper.spiders.parsers.models import ParserResults


def to_proxy(dataclass_factory: DataclassFactory) -> DataclassFactoryProxy:
    return DataclassFactoryProxy(dataclass_factory)


class IDataclassFactory(ABC):  # interface

    @abstractmethod
    def convert(self, results: list[ParserResults]) -> WikiBaseModel:
        pass


class DataclassFactoryProxy(IDataclassFactory):
    """I'm using a factory so that I could hide the other methods without prefixing it with remove_underscores
    Since python doesn't have a good implementation of visibility modifiers
    """

    def __init__(self, dataclass_factory: DataclassFactory):
        self.dataclass_factory = dataclass_factory

    @final
    def convert(self, results: list[ParserResults]) -> WikiBaseModel:
        self.dataclass_factory.convert(results)


class DataclassFactory(IDataclassFactory, ABC):

    @staticmethod
    def results_to_dict(results: list[ParserResults]) -> dict:
        return {parser_result.parser['name']: parser_result.result for parser_result in results}

    @staticmethod
    @abstractmethod
    def build(result: dict) -> WikiBaseModel:
        pass

    @final
    def convert(self, results: list[ParserResults]) -> WikiBaseModel:
        return self.build(self.results_to_dict(results))


class LevellingInformationConverter(DataclassFactory):

    @staticmethod
    def build(result: dict) -> WikiBaseModel:
        return LevellingInformation.parse_obj(result)


class ItemInformationConverter(DataclassFactory):

    @staticmethod
    def build(result: dict) -> WikiBaseModel:
        upgrades_into = result.pop('upgrades into')
        upgrades_from = result.pop('upgrades from')
        result.update({'upgrades': {'from': upgrades_from, 'into': upgrades_into}})
        return ItemLeaf.parse_obj(result)


class MonsterInformationConverter(DataclassFactory):

    @staticmethod
    def build(result: dict) -> WikiBaseModel:
        return MonsterLeaf.parse_obj(result)
