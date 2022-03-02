from typing import TypedDict, Optional

from bson import ObjectId
from pydantic import BaseModel as PydanticBaseModel, BaseConfig

from Utils.generics.strings import remove_underscores
from Utils.types import OptionalStr, IdStringPair

ExpData = TypedDict('ExpData', {'exp': int, 'break status': OptionalStr, 'exp progress': float})


class LevellingConfig(BaseConfig):
    arbitrary_types_allowed = True
    allow_mutation = False
    alias_generator = remove_underscores


class LevellingInformation(PydanticBaseModel):
    mob_type: int
    mob_level: int
    mob_information: IdStringPair
    mob_location: str
    exp_information: ExpData

    class Config(LevellingConfig):
        ...
