import asyncio
from enum import Enum
from typing import Optional, Generator, Union, Any, Callable, TypedDict

import pymongo
from bson.objectid import ObjectId
from phonetics import metaphone
from pydantic.fields import ModelField
from pymongo.collation import Collation, CollationStrength

from .database import Database, ItemNotFound
from .profiler_ import profile

from pydantic import Field, validator, root_validator, ValidationError, PrivateAttr, BaseConfig, HttpUrl, Extra
from pydantic import BaseModel as PydanticBaseModel


def get_exception_from(func: Callable, args) -> Optional[Exception]:
    try:
        func(*args)
    except Exception as exc:
        return exc
    else:
        return


class Grams:

    @staticmethod
    def ngrams(string):
        for i in range(1, len(string) + 1):
            yield string[0:i].lower()

    @staticmethod
    def gram(string, n: int):
        for i in range(n, len(string) + 1):
            yield string[i - n: i].lower()

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


class IterableException(Exception):
    pass


class MissingKeys(IterableException):
    def __init__(self, keys: list[str] = None):
        if keys:
            super().__init__(f'MISSING KEYS: {keys}')
        else:
            super().__init__(f'MISSING KEYS')


class UnIdenticalElements(IterableException):
    def __init__(self, set1, set2):
        super().__init__(f'{set1} | {set2}: are not the same!')


class EmptySlot:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return 'Empty'

    def __len__(self) -> int:
        return 0


Empty = EmptySlot()


class PydanticObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, ObjectId):
            raise TypeError('ObjectId required')
        return str(v)


class EmptyString(Enum):
    EMPTYSTRING = ''


class NamesDict(TypedDict):
    display: str
    raw: str


class ParentsDict(TypedDict):
    category: ObjectId
    item: Union[ObjectId, EmptyString]


class IndexDict(TypedDict, total=False):
    phonetic: str
    ngrams: list[str]
    trigram: list[str]


class WikiConfig(BaseConfig):
    allow_population_by_field_name = True
    arbitrary_types_allowed = True
    extra = Extra.forbid


class WikiObject(PydanticBaseModel):
    object_id: ObjectId = Field(alias='_id')

    def to_dict(self) -> dict:
        return self.dict(by_alias=True)

    @classmethod
    def from_dict(cls, data: dict):
        return cls.parse_obj(data)

    def add_to_database(self, collection: pymongo.collection.Collection):
        if not isinstance(collection, pymongo.collection.Collection):
            raise TypeError(f'Expected {pymongo.collection.Collection} not {collection.__class__}')

        if not (data := self.to_dict()):
            return

        collection.insert_one(data)

    class Config(WikiConfig):
        pass


class Category(WikiObject):
    name: str
    parent: ObjectId = ''
    _children: list['Category'] = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._children = self.get_children_from(object_id=self.object_id)

    @validator('parent')
    def parent_validator(cls, input_value, values):
        if not (parent := input_value):
            try:
                parent = cls.get_parent_category(values['type'])
            except NoParent:
                return ''
        if not isinstance(parent, ObjectId):
            raise TypeError(f'{parent.__class__} is not of the type {ObjectId}')
        if Database.exists(Database.CATEGORIES, {'_id': parent}) is False:  # verifies if parent is valid
            raise ItemNotFound(parent)
        return parent

    def get_children_from(self, object_id) -> list['Category']:
        """
        Returns
        -------
        List of Database Documents of Children
        """
        def find_children() -> list[dict]:
            if children := list(Database.CATEGORIES.find({'parent': object_id})):
                return children
            if children := list(Database.ITEMS.find({'parent': object_id})):
                return children
            raise NoChildren()

        children: list[Category] = [self.from_dict(child) for child in find_children()]
        return children

    @staticmethod
    def get_parent_category(object_id: ObjectId) -> dict:
        """This fetches the parent document of a category, which is also a category

        Returns
        -------
        Database Document of Parent Category
        """
        if not Database.exists(Database.CATEGORIES, {'_id': object_id}):
            raise ItemNotFound(ObjectId)
        if not (parent := Database.CATEGORIES.find_one({'_id': object_id})['parent']):
            raise NoParent()
        return Database.CATEGORIES.find_one({'_id': parent})  # returns database document


class Item(WikiObject):
    names: NamesDict
    parents: ParentsDict
    item_type: str = Field(..., alias='type')

    market_value: dict = {}
    stats: dict = {}
    note: str = ''
    location: list[dict] = []
    recipe: dict = {}
    uses: list[dict] = []
    image: Union[HttpUrl, EmptyString] = ''
    index: IndexDict = {}

    def __eq__(self, other: 'Item'):
        return self.object_id == other.object_id

    def __lt__(self, other: 'Item'):
        return self.names['display'] < other.names['display']

    def __gt__(self, other: 'Item'):
        return self.names['display'] > other.names['display']

    @validator('*', pre=True)
    def set_value_of_empty_fields_to_be_their_types(
            cls, value, values: dict[str, Any], field: ModelField, config: BaseConfig
    ):
        if field.default is None:  # if the field is required
            return value

        for validator_ in field.validators:
            if get_exception_from(validator_, (cls, value, values, field, config)):
                value = field.default

        return value

    @validator('index')
    def check_if_index_is_valid(cls, input_value: dict, values):
        index = {
            'phonetic': metaphone(values['names']['display']),
            'ngrams': list(Grams.ngrams(values['names']['display'])),
            'trigram': list(Grams.trigram(values['names']['display']))
        }
        if not input_value:  # if empty
            input_value = index
        if set(input_value) != set(index):
            def get_keys(dct: dict) -> list[str]:
                return list(dct.keys())
            raise UnIdenticalElements(get_keys(input_value), get_keys(index))

        return input_value

    class Config(WikiConfig):
        allow_mutation = False
        alias_generator = lambda string: string.replace('_', ' ')
        use_enum_values = True


class QueryItem:
    """The Search Engine for the Items Database

    Note:
        Ranking Results by the number of matches
        https://stackoverflow.com/questions/12405837/in-mongodb-search-in-an-array-and-sort-by-number-of-matches
    """

    def __init__(self, item_name: str):
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
                        {'$size': {
                            '$setIntersection': [word.lower().split(), {'$split': [{'$toLower': '$name'}, ' ']}]}},
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

        pipeline_2 = [
            {'$match': {'$text': {'$search': word}}},  # search
            {'$sort': {'score': {'$meta': "textScore"}, 'names.display': 1}}
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
            {'$match': {'rank': {'$gt': 0}}},
            {'$sort': {'rank': -1, 'names.display': 1}}
        ]
        """`rank` is an integer that is derived from the size of the intersected array of `grams` and $index.grams
        """
        return list(Database.ITEMS.aggregate(pipeline))

    async def _results(self) -> Generator[tuple[list, str], None, None]:  # generator
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

    async def get_results(self) -> Optional[list[dict]]:
        """Either returns an list of match\s
        """
        # TODO: Create Collection Collation first before trying anything
        #  (https://docs.atlas.mongodb.com/schema-suggestions/case-insensitive-regex/)

        item_name = self.item_name
        collation = Collation(locale='en', strength=CollationStrength.SECONDARY)
        if exact_match := list(Database.ITEMS.find({'names.display': item_name}).collation(collation)):
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
        return  # TODO: RAISE EXCEPTION INSTEAD

    async def output(self) -> Optional[list[dict]]:
        """This filters out items that are not parent items
        """
        def only_get_parent_items(item: dict):
            return item['names']['display'] == item['names']['raw']
        return list(filter(only_get_parent_items, await self.get_results()))

    @staticmethod
    def query_to_item(results: list[dict]):  # generator
        for item in results:
            yield Item.from_dict(item)
