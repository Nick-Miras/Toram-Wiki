import pymongo.collection
from discord.ext import menus
from bson.objectid import ObjectId
import discord
from typing import Union
from .database import Database, ItemNotFound
import pymongo
from pymongo.collation import Collation, CollationStrength
from phonetics import metaphone
import asyncio


def ngrams(string):
    for i in range(1, len(string) + 1):
        yield string[0:i].lower()


class WikiException(Exception):
    pass


class InvalidCategory(WikiException):
    def __init__(self, category=None):
        category = category if category else 'Category'
        super().__init__(f'{category} is not a valid category.')


class WikiObject:
    def __init__(self, object_id: ObjectId, name: str):
        self.object_id = object_id
        self.name = name
        self._parent = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def object_id(self):
        return self._object_id

    @object_id.setter
    def object_id(self, value):
        self._object_id = value

    def _get_parent(self) -> dict:
        """

        Returns
        -------
        Database Document of Parent
        """
        if not (parent := Database.CATEGORIES.find_one({'_id': self.object_id})['parent']):
            raise Exception  # TODO: Raise NoParent Exception
        return Database.CATEGORIES.find_one({'_id': parent})  # returns database document

    @property
    def parent(self) -> ObjectId:
        return self._parent

    @parent.setter
    def parent(self, value):  # TODO: Decide whether to add this as an __init__ argument
        if value is None:
            value = self._get_parent()

        def verify(value):
            if isinstance(value, dict) and '_id' in value:
                return value['_id']
            if isinstance(value, ObjectId):
                return value
            raise Exception(f'{value} is not a valid Parent')

        value = verify(value)
        if Database.exists(Database.CATEGORIES, {'_id': value}) is False:  # verifies if parent is valid
            raise ItemNotFound(value)
        self._parent = value

    def to_dict(self) -> dict:
        def clean(key):
            return key.replace('_', ' ')

        def replace(value):
            return '' if value is None else value

        data = {
            clean(key): replace(value)
            for key, value in self.__dict__.items()
            if not key.startswith('__')
        }
        return data

    async def add_to_database(self, collection: pymongo.collection.Collection):
        data = self.to_dict()
        collection.insert_one(data)


class Category(WikiObject):
    valid_categories = [
        'category',
        'item'
    ]

    def __init__(self, object_id: ObjectId, name: str, category: str, parent: ObjectId = None):
        super().__init__(object_id, name)
        self.parent = parent
        self.category = category
        self._children = None

    def _get_children(self) -> list[dict]:
        """

        Returns
        -------
        List of Database Documents of Children
        """
        if not (children := list(Database.CATEGORIES.find({'parent': self.object_id}))):
            raise Exception  # TODO: Raise NoChildren Exception
        return children

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if value not in self.valid_categories:
            raise InvalidCategory(value)
        self._category = value

    @property
    def children(self):
        """
        Returns
        -------
        :class:`list[Category]`
            returns a list of Category Objects
        """
        if (children := self._children) is None:
            children = self._get_children()
        data: list[dict] = children
        self._children: list[Category] = [self.from_dict(datum) for datum in data]
        return self._children

    @classmethod
    def from_dict(cls, data: dict):
        assert isinstance(data, dict)  # TODO: Do Verification of Data
        object_id = data.pop('_id')
        self = Category(object_id=object_id, **data)
        return self


class Empty:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return 'Embed.Empty'

    def __len__(self) -> int:
        return 0


class Item(WikiObject):
    __slots__ = (
        'object_id',
        'name',
        'parent',
        'type', '_type',
        'location',
        'note',
        'index', '_index'
    )

    def __init__(self, object_id: ObjectId, name: str, **kwargs):
        super().__init__(object_id, name)
        self.__init_kwargs = __init_kwargs = {
            'parent': kwargs.get('parent', Empty),
            'type': kwargs.get('type', Empty),
            'location': kwargs.get('location', Empty),
            'note': kwargs.get('note', None),
            'index': kwargs.get('index', {})
        }

        if Empty in __init_kwargs.values():
            empty_arguments = ' '.join(key for key, value in __init_kwargs.items() if isinstance(value, Empty))
            raise Exception(f'Keys: {empty_arguments} cannot have empty arguments')

        for key, value in __init_kwargs:
            setattr(self, key, value)

    @property
    def index(self) -> dict:
        return self._index

    @index.setter
    def index(self, index: dict):
        if not isinstance(index, dict):
            raise TypeError(f'{index} is not type:`dict`')
        if not index:  # if the dictionary is empty\
            # TODO: Decide whether to use a list of dictionaries instead of only using a single dictionary
            index = {
                'phonetic': metaphone(self.name),
                'ngrams': ngrams(self.name),
            }
        self._index = index

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):  # TODO: Add authentication for :param: value
        self._type = value


class QueryItem:
    """The Search Engine for the Items Database

    Note:
        Ranking Results by the number of matches
        https://stackoverflow.com/questions/12405837/in-mongodb-search-in-an-array-and-sort-by-number-of-matches
    """
    def __init__(self, item_name):
        self.item_name = item_name

    @staticmethod
    async def _query_phonetic(word) -> dict:  # rank 1
        pipeline = [
            {'$match': {'index.phonetic': metaphone(word)}},
            {'$project': {
                '_id': True,
                'name': True
            }}
        ]
        for result in Database.ITEMS.aggregate(pipeline):
            yield result

    @staticmethod
    async def _query_text(word) -> dict:  # rank 2
        pipeline = [
            {'$match': {'$text': {'$search': word}}},  # search
            {'$project': {
                '_id': True,
                'name': True,
                'rank': {'$size': {
                        '$setIntersection': [word.lower().split(), {'$split': [{'$toLower': '$name'}, ' ']}]
                    }}
            }
            },
            {'$sort': {'rank': -1}}
        ]
        """The `rank` field is an integer that is derived from the size of the intersected array of word.lower().split() 
        and the $name.lower().split()
        """
        for result in Database.ITEMS.aggregate(pipeline):
            yield result

    @staticmethod
    async def _query_ngrams(word) -> dict:  # rank 3
        # TODO: Check if this actually works
        grams = list(ngrams(word))
        pipeline = [
            {'$match': {'index.ngrams': {'$in': grams}}},  # search
            {'$project': {
                '_id': True,
                'name': True,
                'rank': {'$size': {
                    '$setIntersection': [grams, '$index.ngrams']
                }}
            }
             },
            {'$sort': {'rank': -1}}
        ]
        """`rank` is an integer that is derived from the size of the intersected array of `grams` and $index.grams
        """
        for result in Database.ITEMS.aggregate(pipeline):
            yield result

    async def _results(self) -> tuple[list, str]:  # generator
        """Runs all three query generators together. 
        Not minding if the item has already been found in higher rank search engines.
        """  # probably not going to use this

        # returns (list[dict], __name_of_function__)
        item_name = self.item_name

        async def wrapper(coro):
            return [i async for i in coro], coro.__name__.replace('_query_', '')

        coros = [self._query_ngrams(item_name), self._query_text(item_name), self._query_phonetic(item_name)]
        __tasks = [asyncio.create_task(wrapper(coro)) for coro in coros]
        done, _ = await asyncio.wait(__tasks, return_when=asyncio.ALL_COMPLETED)

        for task in done:
            yield task.result()

    async def output(self) -> list[dict]:
        """Either returns an list of match\s
        """
        # TODO: Create Collection Collation first before trying anything
        #  (https://docs.atlas.mongodb.com/schema-suggestions/case-insensitive-regex/)

        item_name = self.item_name
        collation = Collation(locale='en', strength=CollationStrength.SECONDARY)
        if exact_match := list(Database.ITEMS.find({'name': item_name}).collation(collation)):
            return exact_match
        if phrase_match := list(Database.ITEMS.find({'$text': {'$search': f'\"{item_name}\"'}})):
            return phrase_match
        # from here on, exact word matching is exhausted so we will have to find other ways to match the query
        if phonetic_match := [result async for result in self._query_phonetic(item_name)]:
            return phonetic_match
        if text_search_match := [result async for result in self._query_text(item_name)]:
            return text_search_match
        if ngrams_match := [result async for result in self._query_ngrams(item_name)]:
            return ngrams_match



