from abc import ABC, abstractmethod
from typing import Type

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class ScraperProcess(ABC):

    def __init__(self):
        self.process = CrawlerProcess(get_project_settings())

    @abstractmethod
    def start(self, scraper, *args, **kwargs):
        """Injects the arguments into the scrapers and runs the scrapers
        """


class SingleScraper(ScraperProcess):
    def start(self, scraper: scrapy.Spider.__class__, *args, **kwargs):
        """Injects the arguments into the scraper and runs the scraper
        """
        self.process.crawl(scraper(*args, **kwargs).__class__, *args, **kwargs)
        self.process.start()


class MultiScraper(ScraperProcess):
    def start(self, scraper: list[Type[scrapy.Spider]], *args, **kwargs):
        """Injects the arguments into the scrapers and runs the scrapers
        """
        for scraper in scraper:
            self.process.crawl(scraper(*args, **kwargs).__class__, *args, **kwargs)
        self.process.start()
