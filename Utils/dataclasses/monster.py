from typing import Optional

from bson import ObjectId
from pydantic import Field, HttpUrl, validator

from Utils.dataclasses.abc import WikiBaseModel, IdType, Difficulty, Element, ItemType, DyeType
from Utils.types import IdStringPair


class MonsterDrop(WikiBaseModel):
    item_type: ItemType = Field(..., alias='type')
    name: IdStringPair
    dye: Optional[DyeType]


class MonsterLeaf(WikiBaseModel):
    id: Optional[IdType] = Field(default_factory=ObjectId, alias='_id')
    name: str
    level: int
    difficulty: Optional[Difficulty] = None
    hp: Optional[int] = None
    element: Optional[Element] = None
    exp: Optional[int] = None
    tamable: bool
    location: IdStringPair
    drops: list[MonsterDrop]
    image: Optional[HttpUrl] = None

    @validator('id')
    def to_object_id(cls, value):
        return value or ObjectId()


class MonsterCompositeLeaf(WikiBaseModel):
    monster_composite_leaf_id: Optional[IdType] = Field(default_factory=ObjectId, alias='_id')
    level: int
    difficulty: Optional[Difficulty]

    @validator('monster_composite_leaf_id')
    def to_object_id(cls, value):
        return value or ObjectId()


class MonsterComposite(WikiBaseModel):
    monster_composite_id: Optional[IdType] = Field(default_factory=ObjectId, alias='_id')
    name: str
    location: IdStringPair
    leaves: list[MonsterCompositeLeaf]

    @validator('monster_composite_id')
    def to_object_id(cls, value):
        return value or ObjectId()
