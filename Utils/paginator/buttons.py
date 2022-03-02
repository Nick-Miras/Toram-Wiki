from abc import ABC, abstractmethod
from typing import Optional, Union

from nextcord import ButtonStyle, Emoji, Interaction, SelectOption
from nextcord.types.emoji import PartialEmoji
from nextcord.ui import Select, Button
from nextcord.utils import MISSING
from pydantic import BaseModel as PydanticBaseModel


class BetterButton(ABC, PydanticBaseModel, Button):
    style: ButtonStyle = ButtonStyle.secondary
    label: Optional[str] = None
    disabled: bool = False
    custom_id: Optional[str] = None
    url: Optional[str] = None
    emoji: Optional[Union[str, Emoji, PartialEmoji]] = None
    row: Optional[int] = None

    @abstractmethod
    async def callback(self, interaction: Interaction):
        ...


class BetterSelectOption(ABC, PydanticBaseModel, Select):
    label: str
    value: str = MISSING
    description: Optional[str] = None
    emoji: Optional[Union[str, Emoji, PartialEmoji]] = None
    default: bool = False


class BetterSelect(ABC, PydanticBaseModel, Select):
    custom_id: str = MISSING
    placeholder: Optional[str] = None
    min_values: int = 1
    max_values: int = 1
    options: list[SelectOption] = MISSING
    disabled: bool = False
    row: Optional[int] = None
