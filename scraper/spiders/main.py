"""in case if developer wants to scraper manually"""
import pprint
from abc import ABC, abstractmethod
from typing import final

from pydantic import BaseModel
from scrapyscript import Job as ScrapyJob, Processor as ScrapyProcessor

from Utils.generics import split_by_chunk
from database import get_mongodb_client
from database.command.write import InsertMany, DatabaseOperations
from database.models import WhiskeyDatabase
from scraper.spiders.converters import ItemInformationConverter, MonsterInformationConverter
from scraper.spiders.parsers.coryn.item import ItemCompositeParser
from scraper.spiders.parsers.coryn.monster import MonsterCompositeParser
from scraper.spiders.scrapers import ScraperInformation
from scraper.spiders.scrapers.concrete_scrapers import CorynScraper


class Scrape(ABC):

    def __init__(self):
        self.mongodb_client = get_mongodb_client()

    @staticmethod
    @abstractmethod
    def get_scraper_information() -> ScraperInformation:
        pass

    @staticmethod
    @abstractmethod
    def process_results(results: list[dict]) -> None:
        """ function called to process the results returned from scraping
        Args:
            results: the results returned from the scraped objects
        """

    @final
    def start(self):
        processor = ScrapyProcessor(settings=None)
        job = ScrapyJob(CorynScraper, self.get_scraper_information())
        self.process_results(processor.run(job))
        print('Finished')


class ScrapeCorynWithResultProcess(Scrape):

    @staticmethod
    def get_scraper_information() -> ScraperInformation:
        return ScraperInformation(
            url='https://coryn.club/item.php?&show=250&order=name&p=0',
            parser=ItemCompositeParser,
            next_page=True,
            converter=ItemInformationConverter()
        )

    def process_results(self, results: list[dict[str, BaseModel]]):
        whiskey_database = WhiskeyDatabase(self.mongodb_client)
        controller = DatabaseOperations(whiskey_database.items_leaf_mementos)
        collection = whiskey_database.items_leaf
        results: list[list[dict[str, BaseModel]]] = split_by_chunk(results, 250)
        for result_batch in results:
            data = list(result['result'].dict(by_alias=True) for result in result_batch)
            command = InsertMany(collection=collection, data=data)
            controller.register(command)


class ScrapeCorynRaw(Scrape):

    @staticmethod
    def get_scraper_information() -> ScraperInformation:
        return ScraperInformation(
            url='https://coryn.club/monster.php?&show=250&order=name&p=0',
            parser=MonsterCompositeParser,
            next_page=True,
            converter=MonsterInformationConverter()
        )

    @staticmethod
    def process_results(results: list[dict]) -> None:
        for result in results:
            pprint.pprint(result['result'].dict(by_alias=True))


class MonsterMassScrape(Scrape):
    @staticmethod
    def get_scraper_information() -> ScraperInformation:
        return ScraperInformation(
            url='https://coryn.club/monster.php?&show=250&order=name&p=0',
            parser=MonsterCompositeParser,
            next_page=True,
            converter=MonsterInformationConverter()
        )

    def process_results(self, results: list[dict[str, BaseModel]]):
        whiskey_database = WhiskeyDatabase(self.mongodb_client)
        collection = whiskey_database.monsters_leaf
        collection.insert_many(list(result['result'].dict(by_alias=True) for result in results))


class ItemMassScrape(Scrape):
    @staticmethod
    def get_scraper_information() -> ScraperInformation:
        return ScraperInformation(
            url='https://coryn.club/item.php?&show=250&order=name&p=0',
            parser=ItemCompositeParser,
            next_page=True,
            converter=ItemInformationConverter()
        )

    def process_results(self, results: list[dict[str, BaseModel]]):
        whiskey_database = WhiskeyDatabase(self.mongodb_client)
        collection = whiskey_database.items_leaf
        collection.insert_many(list(result['result'].dict(by_alias=True) for result in results))


if __name__ == '__main__':
    MonsterMassScrape().start()
