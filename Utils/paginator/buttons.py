import os
from abc import ABC, abstractmethod
from typing import Optional

from discord import ButtonStyle, Interaction, SelectOption
from discord.ui import Select, Button
from pydantic import BaseConfig, Field
from pydantic import BaseModel as PydanticBaseModel

from Utils.types import DiscordEmoji
from .page.tree import PageTreeController


class ButtonConfig(BaseConfig):
    arbitrary_types_allowed = True


class ButtonData(ABC, PydanticBaseModel):
    custom_id: Optional[str] = None
    style: ButtonStyle = ButtonStyle.secondary
    label: Optional[str] = None
    disabled: bool = False
    url: Optional[str] = None
    emoji: Optional[DiscordEmoji] = None
    row: Optional[int] = None

    class Config(ButtonConfig):
        pass


class SelectContainerData(PydanticBaseModel):
    custom_id: str = Field(default_factory=os.urandom(16).hex)
    placeholder: Optional[str] = None
    min_values: int = 1
    max_values: int = 1
    options: list[SelectOption] = []
    disabled: bool = False
    row: Optional[int] = None

    class Config(ButtonConfig):
        pass


class BetterSelectButton(ABC, Button):
    def __init__(self, controller: PageTreeController, data: ButtonData):
        super().__init__(**data.dict())
        self.controller = controller

    @abstractmethod
    async def callback(self, interaction: Interaction):
        pass


class BetterSelectContainer(ABC, Select):
    def __init__(self, controller: PageTreeController, data: SelectContainerData):
        super().__init__(**data.dict())
        self.controller = controller

    @abstractmethod
    async def callback(self, interaction: Interaction):
        pass


class GoBack(BetterSelectButton):
    def __init__(self, controller):
        super().__init__(controller=controller, data=ButtonData(emoji="🔙", style=ButtonStyle.blurple))

    async def callback(self, interaction: Interaction):
        self.controller.goto_parent()


class GoBackTwice(BetterSelectButton):
    def __init__(self, controller):
        super().__init__(controller=controller, data=ButtonData(emoji="🔙", style=ButtonStyle.blurple))

    async def callback(self, interaction: Interaction):
        self.controller.goto_parent()
        self.controller.goto_parent()


class GoLeft(BetterSelectButton):
    def __init__(self, controller):
        super().__init__(controller=controller, data=ButtonData(emoji="⬅️", style=ButtonStyle.blurple))

    async def callback(self, interaction: Interaction):
        self.controller.goto_previous_sibling()


class GoRight(BetterSelectButton):
    def __init__(self, controller):
        super().__init__(controller=controller, data=ButtonData(emoji="➡️", style=ButtonStyle.blurple))

    async def callback(self, interaction: Interaction):
        self.controller.goto_next_sibling()


class GoFirst(BetterSelectButton):
    def __init__(self, controller):
        super().__init__(controller=controller, data=ButtonData(emoji="⏮️", style=ButtonStyle.blurple))

    async def callback(self, interaction: Interaction):
        self.controller.goto_first_sibling()


class GoLast(BetterSelectButton):
    def __init__(self, controller):
        super().__init__(controller=controller, data=ButtonData(emoji="⏭️", style=ButtonStyle.blurple))

    async def callback(self, interaction: Interaction):
        self.controller.goto_last_sibling()
