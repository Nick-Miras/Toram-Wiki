from typing import Optional

import scrapy

from scraper.spiders.exceptions import InvalidUrl
from scraper.spiders.scrapers import Scraper


class CorynScraper(Scraper):
    name = 'coryn'

    @staticmethod
    def verify_url(url: str) -> list[str]:
        if url.startswith('https://coryn.club') is False:
            raise InvalidUrl(url)
        return [url]

    def get_next_page(self, response) -> Optional[scrapy.Request]:
        button_container = response.css('div.pagination-group-btn a')
        for button in button_container:
            if button.xpath('./i[@class="fas fa-angle-right"]').get() is not None:
                if (button := button.xpath('@href').get()) is not None:
                    return response.follow(button, callback=self.parse)
