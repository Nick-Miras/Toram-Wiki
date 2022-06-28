from __future__ import annotations

from enum import Enum
from typing import Optional, TypeAlias

from bson import ObjectId
from pydantic import HttpUrl, Field, validator

from .abc import WikiBaseModel, WikiBaseConfig, ItemType, IdType, DyeType
from ..generics import remove_duplicates
from ..generics.strings import remove_underscores
from ..types import IdStringPair

OptionalInt = Optional[int]
OptionalStr = Optional[str]
StringOrInt = str | int


def return_default_image(item_type: ItemType) -> str:
    match item_type:
        case ItemType.ArmorCrysta:
            return "https://cdn.discordapp.com/emojis/952712290828963902.webp?size=4096&quality=lossless"
        case ItemType.NormalCrysta:
            return "https://cdn.discordapp.com/emojis/952712291160322129.webp?size=4096&quality=lossless"
        case ItemType.SpecialCrysta:
            return "https://cdn.discordapp.com/emojis/677105475627515904.webp?size=4096&quality=lossless"
        case ItemType.WeaponCrysta:
            return "https://cdn.discordapp.com/emojis/952712291118370826.webp?size=4096&quality=lossless"
        case ItemType.AdditionalCrysta:
            return "https://cdn.discordapp.com/emojis/952712291093209148.webp?size=4096&quality=lossless"
        case ItemType.EnhancerCrystaRed:
            return ""
        case ItemType.EnhancerCrystaBlue:
            return ""
        case ItemType.EnhancerCrystaGreen:
            return ""
        case ItemType.EnhancerCrystaPurple:
            return ""
        case ItemType.EnhancerCrystaYellow:
            return ""

        # weapons
        case ItemType.Dagger:
            return "https://cdn.discordapp.com/attachments/432408793998163968/816542734265221120/PicsArt_03-03-01.28.24.png"
        case ItemType.Katana:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234037033697290/IMG_20201013_065623.png"
        case ItemType.Arrow:
            return "https://cdn.discordapp.com/attachments/432408793998163968/816578870420439081/1614757958509.png"
        case ItemType.MagicDevice:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234037772156960/IMG_20201013_063412.png"
        case ItemType.OneHandedSword:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234038539190272/IMG_20201013_063118.png"
        case ItemType.TwoHandedSword:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234038761881665/IMG_20201013_063020.png"
        case ItemType.Staff:
            return "https://cdn.discordapp.com/attachments/432408793998163968/787587412237746181/650557657564053519.png"
        case ItemType.Halberd:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234036454621184/IMG_20201013_084126.png"
        case ItemType.Bow:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234036719648808/IMG_20201013_083622.png"
        case ItemType.Bowgun:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234037499920418/IMG_20201013_063539.png"
        case ItemType.Knuckles:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234036136509500/IMG_20201013_084804.png"
        case ItemType.Shield:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788234432246448148/IMG_20201013_083854.png"

        # equipment
        case ItemType.SpecialGear:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788352419712860180/IMG_20201013_174953.png"
        case ItemType.AdditionalGear:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788352419443769374/IMG_20201013_175047.png"
        case ItemType.Armor:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788352420328767498/IMG_20201013_174251.png"

        # others
        case ItemType.Usable:
            return "https://cdn.discordapp.com/emojis/650557983800950795.webp?size=4096&quality=lossless"
        case ItemType.Material:
            return ""
        case ItemType.Gem:
            return "https://cdn.discordapp.com/attachments/740178985589145684/789755110875201556/IMG_20201216_165213.png"
        case ItemType.RefinementSupport:
            return ""
        case ItemType.Piercer:
            return "https://cdn.discordapp.com/attachments/654287868612575263/789740560047013929/IMG_20201219_115652.png"
        case ItemType.Ore:
            return "https://cdn.discordapp.com/attachments/740178985589145684/788053476244324382/IMG_20201013_090044.png"


class RequirementType(Enum):
    HeavyArmor = 'Heavy Armor'
    LightArmor = 'Light Armor'
    DualSwords = 'Dual Swords'
    Staff = 'Staff'
    MagicDevice = 'Magic Device'
    Bow = 'Bow'
    Shield = 'Shield'
    Event = 'Event'
    Dagger = 'Dagger'
    TwoHandedSword = '2-Handed Sword'
    OneHandedSword = '1-Handed Sword'
    Katana = 'Katana'
    Knuckle = 'Knuckle'
    Bowgun = 'Bowgun'
    AdditionalGear = 'Additional Gear'
    Arrow = 'Arrow'
    SpecialGear = 'Special Gear'
    Halberd = 'Halberd'
    Armor = 'Armor'


RequirementTypeSequence: TypeAlias = list[RequirementType]


def get_requirement_type(partial_type: str) -> RequirementTypeSequence:
    return remove_duplicates(RequirementType(_) for _ in partial_type.split(','))


class MarketValueDict(WikiBaseModel):
    sell: OptionalInt
    process: OptionalStr
    duration: OptionalStr


class MaterialsDict(WikiBaseModel):
    amount: int
    item: IdStringPair


class RecipeDict(WikiBaseModel):
    fee: OptionalInt
    set: int
    level: OptionalInt
    difficulty: int
    materials: list[MaterialsDict]


class LocationDict(WikiBaseModel):
    monster: Optional[IdStringPair]  # monster id and display string
    dye: Optional[DyeType]
    map: Optional[IdStringPair]  # map id and display string


class UsesDict(WikiBaseModel):
    type: str
    items: list[IdStringPair]


class StatsDict(WikiBaseModel):
    requirement: Optional[RequirementTypeSequence]
    attributes: list[tuple[str, float]]


class UpgradesDict(WikiBaseModel):
    upgrades_from: Optional[list[IdStringPair]] = Field(..., alias='from')
    upgrades_into: Optional[list[IdStringPair]] = Field(..., alias='into')


class ItemLeaf(WikiBaseModel):
    id: Optional[IdType] = Field(default_factory=ObjectId, alias='_id')
    name: str
    type: Optional[ItemType]
    market_value: MarketValueDict
    image: Optional[HttpUrl] = None
    stats: Optional[list[StatsDict]] = None
    location: Optional[list[LocationDict]] = None
    recipe: Optional[RecipeDict] = None
    uses: Optional[list[UsesDict]] = None
    upgrades: Optional[UpgradesDict] = None

    @validator('id')
    def to_object_id(cls, value):
        return value or ObjectId()

    class Config(WikiBaseConfig):
        alias_generator = remove_underscores


class ItemCompositeLeaf(WikiBaseModel):
    item_composite_leaf_id: Optional[IdType] = Field(default_factory=ObjectId, alias='_id')
    difference: str
    has_dye: bool

    @validator('item_composite_leaf_id')
    def to_object_id(cls, value):
        return value or ObjectId()


class ItemComposite(WikiBaseModel):
    item_composite_id: Optional[IdType] = Field(default_factory=ObjectId, alias='_id')
    name: str
    leaves: list[ItemCompositeLeaf]

    @validator('item_composite_id')
    def to_object_id(cls, value):
        return value or ObjectId()
