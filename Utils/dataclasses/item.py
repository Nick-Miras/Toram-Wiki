from enum import Enum
from typing import Optional, Union, Any, Callable, TypedDict

import pymongo
from bson.objectid import ObjectId
from phonetics import metaphone
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, validator, PrivateAttr, BaseConfig, HttpUrl
from pydantic.fields import ModelField

from .. import Database
from ..database.exceptions import ItemNotFound
from ..generics.strings import Grams
from ..types import StringOrInt, IdStringPair, OptionalStr, OptionalInt, StringStringPair


def get_exception_from(func: Callable, args) -> Optional[Exception]:
    try:
        func(*args)
    except Exception as exc:
        return exc
    else:
        return


class WikiException(Exception):
    ...


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
    ...


class MissingKeys(IterableException):
    def __init__(self, keys: list[str] = None):
        if keys:
            super().__init__(f'MISSING KEYS: {keys}')
        else:
            super().__init__(f'MISSING KEYS')


class UnIdenticalElements(IterableException):
    def __init__(self, set1, set2):
        super().__init__(f'{set1} | {set2}: are not the same!')


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


class WikiConfig(BaseConfig):
    allow_population_by_field_name = True
    arbitrary_types_allowed = True
    # extra = Extra.forbid


class WikiObject(PydanticBaseModel):
    object_id: ObjectId = Field(alias='_id')

    def to_dict(self) -> dict:
        return self.dict(by_alias=True, exclude={'rank'})

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
        ...


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


class NamesDict(TypedDict):  # TODO: TO BE CHANGED
    display: str
    raw: str


class ParentsDict(TypedDict):  # TODO: TO BE CHANGED
    category: ObjectId
    item: Union[ObjectId, EmptyString]


class MarketValueDict(TypedDict):
    sell: OptionalInt
    process: OptionalStr


class IndexDict(TypedDict, total=False):  # TODO: TO BE CHANGED
    phonetic: str
    ngrams: list[str]
    trigram: list[str]


class MaterialsDict(TypedDict):
    amount: int
    item: Union[IdStringPair, tuple[None, str]]  # for mats


class RecipeDict(TypedDict):
    fee: OptionalInt
    set: int
    level: OptionalInt
    difficulty: int
    materials: list[MaterialsDict]


class LocationDict(TypedDict):
    monster: Optional[IdStringPair]  # monster id and display string
    dye: Optional[tuple[StringOrInt, StringOrInt, StringOrInt]]
    map: Optional[IdStringPair]  # map id and display string


class UsesDict(TypedDict):
    type: str
    items: list[IdStringPair]


class Item(WikiObject):
    names: NamesDict
    parents: ParentsDict
    item_type: str = Field(..., alias='type')

    market_value: MarketValueDict = {}
    stats: dict = {}
    note: str = ''
    location: list[dict] = []
    recipe: dict = {}
    uses: list[dict] = []
    image: Union[HttpUrl, EmptyString] = ''
    index: IndexDict = {}
    rank: Optional[int] = None

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
