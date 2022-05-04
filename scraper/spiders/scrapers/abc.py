from abc import ABC, abstractmethod
from typing import Optional, Generator

import scrapy

from Utils.dataclasses.abc import WikiBaseModel
from scraper.spiders.parsers.models import ParserResults
from scraper.spiders.scrapers import models


class Scraper(scrapy.Spider, ABC):
    name: str

    def __init__(self, scraper_information: models.ScraperInformation):
        self.start_urls = self.verify_url(scraper_information.url)  # always before super function
        self.parser = scraper_information.parser
        self.container_path = scraper_information.container_path
        self.converter = scraper_information.converter
        self.next_page: bool = scraper_information.next_page
        super().__init__()

    @staticmethod
    @abstractmethod
    def verify_url(url: str) -> list[str]:
        """Raises an error if url is invalid, else :returns:list[str]"""

    @abstractmethod
    def get_next_page(self, response) -> Optional[scrapy.Request]:
        pass

    def parse(self, response) -> Generator[dict | scrapy.Request, None, None]:
        for result in self.parser(self.container_path, self.converter).parse(response):
            # type: list[ParserResults] | WikiBaseModel

            yield {'result': result}
            # if isinstance(result, WikiBaseModel):
            #     yield PydanticResultWrapper(result=result)
            # else:
            #     yield ParserResultWrapper(result=result)

        if self.next_page is True:
            yield self.get_next_page(response)
