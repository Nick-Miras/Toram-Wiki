"""
Item Search
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Generator

from phonetics import metaphone
from pymongo.collation import Collation, CollationStrength

from Utils.database import Database
from Utils.database.exceptions import ItemNotFound
from Utils.dataclasses.item import Item
from Utils.generics.strings import Grams


class QueryMethod(ABC):
    """The Search Engine for the Items Database

    Note:
        Ranking Results by the number of matches
        https://stackoverflow.com/questions/12405837/in-mongodb-search-in-an-array-and-sort-by-number-of-matches
    """

    @staticmethod
    @abstractmethod
    def query(item_name: str) -> list[dict]: ...


class ExactMatch(QueryMethod):
    collation = Collation(locale='en', strength=CollationStrength.SECONDARY)

    @staticmethod
    def query(item_name: str) -> list[dict]:
        return list(Database.ITEMS.find({'names.display': item_name}).collation(ExactMatch.collation))


class PhoneticSearch(QueryMethod):
    """
    Searching for Rhyming words
    """

    @staticmethod
    def query(item_name: str) -> list[dict]:  # rank 1
        pipeline = [
            {'$match': {'index.phonetic': metaphone(item_name)}}
        ]  # removed project
        return list(Database.ITEMS.aggregate(pipeline))


class PhraseMatch(QueryMethod):

    @staticmethod
    def query(item_name: str) -> list[dict]:
        return list(Database.ITEMS.find({'$text': {'$search': f'\"{item_name}\"'}}))


class TextSearchMethod(QueryMethod, ABC):
    """
    Uses MongoDB textsearch
    """


class TextSearch1(TextSearchMethod):

    @staticmethod
    def query(item_name: str) -> list[dict]:
        pipeline = [
            {'$match': {'$text': {'$search': item_name}}},  # search
            {'$addFields': {'rank': {  # TODO: Verify if the Round and Divide Operators are required
                '$round': [
                    {'$divide': [
                        {'$size': {
                            '$setIntersection': [item_name.lower().split(), {'$split': [{'$toLower': '$name'}, ' ']}]}},
                        {'$size': {'$split': [{'$toLower': '$name'}, ' ']}}
                    ]},
                    2
                ]
            }
            }
            },
            {'$match': {'rank': {'$gt': 0}}},
            {'$sort': {'rank': -1, 'names.display': 1}}
        ]
        # The `rank` field is an integer that is derived from the size of the intersected array of word.lower().split()
        # and the $name.lower().split()
        return list(Database.ITEMS.aggregate(pipeline))


class TextSearch2(TextSearchMethod):
    """Just Shorter"""

    @staticmethod
    def query(item_name: str) -> list[dict]:
        pipeline = [
            {'$match': {'$text': {'$search': item_name}}},  # search
            {'$sort': {'score': {'$meta': "textScore"}, 'names.display': 1}}
        ]
        return list(Database.ITEMS.aggregate(pipeline))


class NGramSearch(QueryMethod):
    """
    Use ngram search and rank results by set intersection
    """

    @staticmethod
    def query(item_name: str) -> list[dict]:
        grams = list(Grams.trigram(item_name))
        pipeline = [
            {'$match': {'index.trigram': {'$in': grams}}},  # search
            {'$addFields': {'rank': {  # TODO: Verify if the Round Operator is required
                '$round': [
                    {'$divide': [
                        {'$size': {'$setIntersection': [grams, '$index.trigram']}},
                        {'$size': '$index.trigram'}
                    ]},
                    2
                ]
            }
            }
            },
            {'$match': {'rank': {'$gt': 0}}},
            {'$sort': {'rank': -1, 'names.display': 1}}  # sort by rank then name
        ]
        # `rank` is an integer that is derived from the size of the intersected array of `grams` and $index.grams
        return list(Database.ITEMS.aggregate(pipeline))


class QueryItem:
    """The Search Engine for the Items Database

    Note:
        Ranking Results by the number of matches
        https://stackoverflow.com/questions/12405837/in-mongodb-search-in-an-array-and-sort-by-number-of-matches
    """

    def __init__(self, item_name: str):
        self.item_name = item_name

    async def _results(self) -> Generator[tuple[list, str], None, None]:  # generator
        """Runs all three query generators together. 
        Not minding if the item has already been found in higher rank search engines.
        """  # probably not going to use this

        # returns (list[dict], __name_of_function__)
        item_name = self.item_name

        async def wrapper(coro):
            return [i async for i in coro], coro.__name__.replace('_query_', '')

        coros = [PhoneticSearch.query(item_name), TextSearch2.query(item_name), NGramSearch.query(item_name)]
        __tasks = [asyncio.create_task(wrapper(coro)) for coro in coros]
        done, _ = await asyncio.wait(__tasks, return_when=asyncio.ALL_COMPLETED)

        for task in done:
            yield task.result()

    async def get_results(self) -> Optional[list[dict]]:
        """Either returns a list of match\s
        """
        # TODO: Create Collection Collation first before trying anything
        #  (https://docs.atlas.mongodb.com/schema-suggestions/case-insensitive-regex/)
        # TODO: Check if shows good results based on feedbacks on Mors Certa discord server
        # TODO: Maybe implement `chain of responsibility` design pattern

        item_name = self.item_name
        if phrase_match := PhraseMatch.query(item_name):
            return phrase_match
        # from here on, exact word matching is exhausted, so we will have to find other ways to match the query
        if text_search_match := TextSearch2.query(item_name):
            return text_search_match
        if ngrams_match := NGramSearch.query(item_name):
            return ngrams_match
        raise ItemNotFound(item_name)

    async def output(self) -> Optional[list[dict]]:
        """This filters out items that are not parent items
        """
        def only_get_parent_items(item: dict):
            return item['names']['display'] == item['names']['raw']
        return list(filter(only_get_parent_items, await self.get_results()))

    @staticmethod
    def query_to_item(results: list[dict]) -> Generator[Item, None, None]:  # generator
        """Turns Query results into :class:`Item`
        """
        for item in results:
            yield Item.from_dict(item)
