from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Type

from discord import ui
from pydantic import BaseModel as PydanticBaseModel

from .tree import PageDataTree
from ...dataclasses.discord import ContentData

D = TypeVar('D')


class PageDataTreeDecorator(ABC, Generic[D]):
    def __init__(self, tree: PageDataTree):
        self.tree: PageDataTree = tree

    @abstractmethod
    def get_data(self) -> D:
        pass


class ContentDisplay(PageDataTreeDecorator[ContentData], ABC):
    pass


class ItemsDisplay(PageDataTreeDecorator[list[ui.Item]], ABC):
    pass


class DisplayData(PydanticBaseModel):
    items: Optional[Type[ItemsDisplay]] = None
    content: Optional[Type[ContentDisplay]] = None

    class Config:
        arbitrary_types_allowed = True
