from typing import TypedDict

from Utils.types import OptionalStr, IdStringPair
from .abc import WikiBaseConfig, WikiBaseModel
from ..generics.strings import remove_underscores

ExpData = TypedDict('ExpData', {'exp': int, 'break status': OptionalStr, 'exp progress': float})


class LevellingInformation(WikiBaseModel):
    mob_type: str
    mob_level: int
    mob_information: IdStringPair
    mob_location: str
    exp_information: list[ExpData]

    class Config(WikiBaseConfig):
        alias_generator = remove_underscores
