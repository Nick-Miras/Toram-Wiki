from __future__ import annotations

from enum import Enum
from typing import TypedDict, Optional, TypeAlias

from bson import ObjectId
from pydantic import HttpUrl, Field, validator

from .abc import WikiBaseModel, WikiBaseConfig
from ..generics import remove_duplicates
from ..generics.strings import remove_underscores
from ..types import IdStringPair

OptionalInt = Optional[int]
OptionalStr = Optional[str]
StringOrInt = str | int
IdType = int | ObjectId


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


def return_default_image(item_type: ItemType) -> str:
    match item_type:
        # TODO: Finish Inserting URLs
        # crystas
        case ItemType.ArmorCrysta:
            return ""
        case ItemType.NormalCrysta:
            return ""
        case ItemType.SpecialCrysta:
            return ""
        case ItemType.WeaponCrysta:
            return ""
        case ItemType.AdditionalCrysta:
            return ""
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
        case ItemType.Special:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788352419712860180/IMG_20201013_174953.png"
        case ItemType.Additional:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788352419443769374/IMG_20201013_175047.png"
        case ItemType.Armor:
            return "https://cdn.discordapp.com/attachments/654287868612575263/788352420328767498/IMG_20201013_174251.png"

        # others
        case ItemType.Usable:
            return ""
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


def get_item_type(partial_type: str) -> Optional[ItemType]:
    """
    Returns:
        None or ItemType due to Coryn classifying regislets as items without specifying their item types
    """
    try:
        return ItemType(partial_type)
    except ValueError:
        return


class MarketValueDict(TypedDict):
    sell: OptionalInt
    process: OptionalStr
    duration: OptionalStr


class MaterialsDict(TypedDict):
    amount: int
    item: IdStringPair


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


class StatsDict(TypedDict):
    requirement: Optional[RequirementTypeSequence]
    attributes: list[tuple[str, float]]


UpgradesDict = TypedDict('UpgradesDict', {
    'from': Optional[list[IdStringPair]],
    'into': Optional[list[IdStringPair]]
})


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

    class Config(WikiBaseConfig):
        pass


class ItemComposite(WikiBaseModel):
    item_composite_id: Optional[IdType] = Field(default_factory=ObjectId, alias='_id')
    name: str
    leaves: list[ItemCompositeLeaf]

    @validator('item_composite_id')
    def to_object_id(cls, value):
        return value or ObjectId()

    class Config(WikiBaseConfig):
        pass
