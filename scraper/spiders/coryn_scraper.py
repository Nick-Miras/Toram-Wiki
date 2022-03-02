from abc import ABC, abstractmethod
from typing import Optional, Any, Type, overload

import scrapy
from pydantic import BaseModel as PydanticBaseModel, HttpUrl, validator, Field
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from .parsers.abc import BaseParser
from .parsers.container_paths import ContainerPaths
from Utils.types import Empty


class ScraperInformation(PydanticBaseModel):
    """Information that will be used and required by the scraper"""
    url: HttpUrl
    parser: Type[BaseParser] = Field(..., allow_mutation=False)  # uninitialized object
    next_page: bool  # if scraper should access the next page
    container_path: Type[ContainerPaths] = Field(Empty, allow_mutation=False)  # uninitialized object

    @validator('container_path', pre=True, always=True)
    def set_container_path(cls, _, values):
        return values['parser'].container_path

    class Config:
        validate_assignment = True


class CorynScraper(scrapy.Spider):
    name = 'coryn'

    def __init__(self, scraper_information: ScraperInformation):
        self.start_urls = [scraper_information.url]  # always before super function
        self.parser: Type[BaseParser] = scraper_information.parser
        self.container_path: Type[ContainerPaths] = scraper_information.container_path
        self.next_page: bool = scraper_information.next_page
        super().__init__()

    def get_next_page(self, response) -> Optional[scrapy.Request]:
        button_container = response.css('div.pagination-group-btn a')
        for buttons in button_container:
            if buttons.css('a i.fa-angle-right').get() is not None:
                return response.follow(buttons, callback=self.parser)

    def parse(self, response):
        yield from self.parser(response, self.container_path).parse()
        if self.next_page:
            yield self.get_next_page(response)


class ScraperProcess:

    def __init__(self):
        self.process = CrawlerProcess(get_project_settings())

    @overload
    def start(self, scraper: scrapy.Spider.__class__, *args, **kwargs):
        """Injects the arguments into the scraper and runs the scraper
        """
        self.process.crawl(scraper(*args, **kwargs).__class__, *args, **kwargs)
        self.process.start()

    def start(self, scraper: list[Type[scrapy.Spider]], *args, **kwargs):
        """Injects the arguments into the scrapers and runs the scrapers
        """
        for scraper in scraper:
            self.process.crawl(scraper(*args, **kwargs).__class__, *args, **kwargs)
        self.process.start()
