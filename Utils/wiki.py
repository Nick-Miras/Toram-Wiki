from bson.objectid import ObjectId
import asyncio
from typing import Optional

import pymongo
from bson.objectid import ObjectId
from phonetics import metaphone
from pymongo.collation import Collation, CollationStrength

from .database import Database, ItemNotFound
from .profiler_ import profile


class Grams:

    @staticmethod
    def ngrams(string):
        for i in range(1, len(string) + 1):
            yield string[0:i].lower()

    @staticmethod
    def gram(string, n: int):
        for i in range(n, len(string) + 1):
            yield string[i-n: i].lower()

    @classmethod
    def trigram(cls, string):  # generator
        return cls.gram(string, 3)


class WikiException(Exception):
    pass


class NoParent(WikiException):
    def __init__(self, item=None):
        item = item if item else 'Item'
        super().__init__(f'{item} has no parents')


class NoChildren(WikiException):
    def __init__(self, item=None):
        item = item if item else 'Item'
        super().__init__(f'{item} has no children')


class InvalidCategory(WikiException):
    def __init__(self, category=None):
        category = category if category else 'Category'
        super().__init__(f'{category} is not a valid category.')


class WikiObject:
    def __init__(self, object_id: ObjectId, name: str):
        self.object_id: ObjectId = object_id
        self.name: str = name
        self._parent = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not value:
            raise TypeError(f'{value} cannot be empty')
        self._name = value

    @property
    def object_id(self):
        return self._object_id

    @object_id.setter
    def object_id(self, value):
        if not value:
            raise TypeError(f'{value} cannot be empty')
        self._object_id = value

    @staticmethod
    def get_parent(object_id: ObjectId) -> dict:
        """

        Returns
        -------
        Database Document of Parent
        """
        if not (parent := Database.CATEGORIES.find_one({'_id': object_id})['parent']):
            raise NoParent()
        return Database.CATEGORIES.find_one({'_id': parent})  # returns database document

    @property
    def parent(self) -> ObjectId:
        parent = self._parent
        if not parent:
            try:
                parent = self.get_parent(self.object_id)
            except NoParent:
                parent = ''
        if not isinstance(parent, ObjectId) and parent != '':
            raise TypeError(f'{parent.__class__} is not of the type {ObjectId}')
        if Database.exists(Database.CATEGORIES, {'_id': parent}) is False:  # verifies if parent is valid
            raise ItemNotFound(parent)
        return parent

    @parent.setter
    def parent(self, value):  # TODO: Decide whether to add this as an __init__ argument
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

    def __init__(self, object_id: ObjectId, name: str, category: str, parent: ObjectId = None):

        super().__init__(object_id, name)
        self.category = category
        self.parent = parent
        self._children = None

    @staticmethod
    def get_children(object_id: ObjectId) -> list[dict]:
        """
        Returns
        -------
        List of Database Documents of Children
        """
        def find_children():
            if children := list(Database.CATEGORIES.find({'parent': object_id})):
                return children
            if children := list(Database.ITEMS.find({'parent': object_id})):
                return children
            raise NoChildren()
        return find_children()

    @property
    def children(self):
        """
        Returns
        -------
        :class:`list[Category]`
            returns a list of Category Objects
        """
        children = self._children
        if children:
            return children
        if children is None:
            children: list[dict] = self.get_children(self.object_id)
            self._children: list[Category] = [self.from_dict(child) for child in children]
            return self._children

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if value not in ['category', 'item']:
            raise InvalidCategory()

        self._category = value

    @classmethod
    @profile
    def from_dict(cls, data: dict):
        if not isinstance(data, dict):
            raise TypeError(f'{data.__class__} is not of the type {dict}')

        __slots = ['_id', 'name', 'parent']
        if all(key in data for key in __slots) is False:
            raise Exception('Missing keys in document')

        self: cls = cls.__new__(cls)

        self.object_id = data.get('_id', Empty)
        self.name = data.get('name', Empty)
        self.parent = data.get('parent', Empty)

        if 'type' in data:
            self.category = 'item'
        else:
            self.category = 'category'

        return self


class EmptySlot:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return 'Empty'

    def __len__(self) -> int:
        return 0


Empty = EmptySlot()


class Item(WikiObject):
    def __init__(
            self,
            object_id: ObjectId,
            name: str,
            item_type,
            parent: ObjectId = None,
            location=None,
            note=None,
            index=None,
            image=None
    ):
        super().__init__(object_id, name)
        self.parent = parent
        self.item_type = item_type
        self.location = location
        self.note = note
        self.index = index
        self.image = image

    @property
    def index(self) -> dict:
        return self._index

    @index.setter
    def index(self, index: dict):
        if not index:
            index = {}
        if not isinstance(index, dict):
            raise TypeError(f'{index} is not type:`dict`')
        if not index:  # if the dictionary is empty
            # TODO: Decide whether to use a list of dictionaries instead of only using a single dictionary
            index = {
                'phonetic': metaphone(self.name),
                'ngrams': list(Grams.ngrams(self.name)),
            }
        self._index = index

    @property
    def item_type(self):
        return self._item_type

    @item_type.setter
    def item_type(self, value):  # TODO: Add authentication for :param: value
        if not value:
            raise TypeError(f'{value} cannot be empty')
        self._item_type = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if not value:
            value = None
        self._location = value

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        if not value:
            value = None
        self._note = value

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, link: str):
        if not link:
            link = None
        self._image = link

    @classmethod
    def from_dict(cls, data: dict):
        if not isinstance(data, dict):
            raise TypeError(f'{data.__class__} is not of the type {dict}')

        __slots = ['_id', 'name', 'type', 'parent', 'location', 'note', 'index', 'image']
        if all(key in data for key in __slots) is False:
            raise Exception('Missing keys in document')

        self: cls = cls.__new__(cls)

        self.object_id = data.get('_id', Empty)
        self.name = data.get('name', Empty)
        self.parent = data.get('parent', None)
        self.item_type = data.get('type', Empty)
        self.location = data.get('location', None)
        self.note = data.get('note', None)
        self.index = data.get('index', {})
        self.image = data.get('image', None)

        return self


class QueryItem:
    """The Search Engine for the Items Database

    Note:
        Ranking Results by the number of matches
        https://stackoverflow.com/questions/12405837/in-mongodb-search-in-an-array-and-sort-by-number-of-matches
    """
    def __init__(self, item_name: str):
        assert isinstance(item_name, str)
        self.item_name = item_name

    @staticmethod
    async def _query_phonetic(word) -> list[dict]:  # rank 1  # TODO: Maybe Remove This
        pipeline = [
            {'$match': {'index.phonetic': metaphone(word)}}
        ]  # removed project
        return list(Database.ITEMS.aggregate(pipeline))

    @staticmethod
    async def _query_text(word) -> list[dict]:  # rank 2
        pipeline = [
            {'$match': {'$text': {'$search': word}}},  # search
            {'$addFields': {'rank': {  # TODO: Verify if the Round and Divide Operators are required
                '$round': [
                    {'$divide': [
                        {'$size': {'$setIntersection': [word.lower().split(), {'$split': [{'$toLower': '$name'}, ' ']}]}},
                        {'$size': {'$split': [{'$toLower': '$name'}, ' ']}}
                    ]},
                    2
                ]
            }
            }
             },
            {'$match': {'rank': {'$gt': 0}}},  # TODO: Verify if this should be added
            {'$sort': {'rank': -1, 'name': 1}}  # TODO: Verify Alphabetical Sort
        ]

        pipeline_2 = [
            {'$match': {'$text': {'$search': word}}},  # search
            {'$sort': {'score': {'$meta': "textScore"}, 'name': 1}}  # TODO: Verify Alphabetical Sort
        ]
        """The `rank` field is an integer that is derived from the size of the intersected array of word.lower().split() 
        and the $name.lower().split()
        """
        return list(Database.ITEMS.aggregate(pipeline_2))

    @staticmethod
    async def _query_ngrams(word) -> list[dict]:  # rank 3
        grams = list(Grams.trigram(word))
        # TODO: Replace the damn name of trigram
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
            {'$match': {'rank': {'$gt': 0}}},  # TODO: Verify if this should be added
            {'$sort': {'rank': -1, 'name': 1}}  # TODO: Verify Alphabetical Sort
        ]
        """`rank` is an integer that is derived from the size of the intersected array of `grams` and $index.grams
        """
        return list(Database.ITEMS.aggregate(pipeline))

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

    async def output(self) -> Optional[list[dict]]:
        """Either returns an list of match\s
        """
        # TODO: Create Collection Collation first before trying anything
        #  (https://docs.atlas.mongodb.com/schema-suggestions/case-insensitive-regex/)

        item_name = self.item_name
        collation = Collation(locale='en', strength=CollationStrength.SECONDARY)
        if exact_match := list(Database.ITEMS.find({'name': item_name}).collation(collation)):
            return exact_match  # should return an array of the size of 1
        if phrase_match := list(Database.ITEMS.find({'$text': {'$search': f'\"{item_name}\"'}})):
            return phrase_match
        # from here on, exact word matching is exhausted so we will have to find other ways to match the query
        if phonetic_match := await self._query_phonetic(item_name):
            return phonetic_match
        if text_search_match := await self._query_text(item_name):
            return text_search_match
        if ngrams_match := await self._query_ngrams(item_name):
            return ngrams_match
        return

    @staticmethod
    def query_to_item(results: list[dict]):  # generator
        for item in results:
            yield Item.from_dict(item)



