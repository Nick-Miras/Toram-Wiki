from __future__ import annotations

from enum import Enum
from typing import Type, Optional, TypeAlias

from bson import ObjectId
from pydantic import BaseModel as PydanticBaseModel, BaseConfig, Extra

from scraper.spiders.parsers.models import ParserResults, ParserResultWrapper

DyeType: TypeAlias = tuple[str | int, str | int, str | int]


class WikiBaseConfig(BaseConfig):
    arbitrary_types_allowed = True
    allow_mutation = False
    extra = Extra.ignore
    use_enum_values = True


class WikiBaseModel(PydanticBaseModel):
    class Config(WikiBaseConfig):
        pass


def dataclass_factory(item: ParserResultWrapper, model: Type[WikiBaseModel]) -> WikiBaseModel:
    """builder for :class:`PydanticBaseModel`"""
    data = {}
    for result in item['result']:
        result = ParserResults.parse_obj(result)
        data.update({result.parser['name']: result.result})

    return model.parse_obj(data)


class ItemType(Enum):
    # Others
    Usable = 'Usable'
    Material = 'Material'
    Gem = 'Gem'
    RefinementSupport = 'Refinement Support'
    Piercer = 'Piercer'
    Ore = 'Ore'

    # Crystas
    ArmorCrysta = 'Armor Crysta'
    NormalCrysta = 'Normal Crysta'
    SpecialCrysta = 'Special Crysta'
    WeaponCrysta = 'Weapon Crysta'
    AdditionalCrysta = 'Additional Crysta'
    EnhancerCrystaRed = 'Enhancer Crysta (Red)'
    EnhancerCrystaBlue = 'Enhancer Crysta (Blue)'
    EnhancerCrystaGreen = 'Enhancer Crysta (Green)'
    EnhancerCrystaPurple = 'Enhancer Crysta (Purple)'
    EnhancerCrystaYellow = 'Enhancer Crysta (Yellow)'

    # Equipment
    SpecialGear = 'Special'
    AdditionalGear = 'Additional'
    Armor = 'Armor'

    # Weapons
    Dagger = 'Dagger'
    Katana = 'Katana'
    Arrow = 'Arrow'
    MagicDevice = 'Magic Device'
    OneHandedSword = '1 Handed Sword'
    TwoHandedSword = '2 Handed Sword'
    Staff = 'Staff'
    Halberd = 'Halberd'
    Bow = 'Bow'
    Bowgun = 'Bowgun'
    Knuckles = 'Knuckles'
    Shield = 'Shield'
    Regislet = 'Regislet'
    NinjutsuScroll = 'Ninjutsu Scroll'


class Element(Enum):
    Dark = 'Dark'
    Fire = 'Fire'
    Water = 'Water'
    Wind = 'Wind'
    Light = 'Light'
    Earth = 'Earth'
    Neutral = 'Neutral'


class Difficulty(Enum):
    Easy = 'Easy'
    Normal = 'Normal'
    Hard = 'Hard'
    Nightmare = 'Nightmare'
    Ultimate = 'Ultimate'


IdType = int | ObjectId


def get_item_type(partial_type: str) -> Optional[ItemType]:
    """
    Returns:
        None or ItemType due to Coryn classifying regislets as items without specifying their item types
    """
    try:
        return ItemType(partial_type)
    except ValueError:
        return
