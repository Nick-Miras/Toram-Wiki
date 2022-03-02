from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic, Union, final
from uuid import uuid4, UUID

from nextcord import ui
from pydantic import BaseModel as PydanticBaseModel, Field

from Utils.paginator.exceptions import ChildNotFound

T = TypeVar('T')
D = TypeVar('D')

ItemList = list[ui.Item]


class NodeInformation(PydanticBaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str


class PageDataNode(ABC, Generic[T, D]):
    def __init__(self, information: NodeInformation, data: D):
        self.id = information.id
        self.name = information.name
        self.data: D = data
        self.parent: Optional[PageDataNode] = None
        self.children: list[PageDataNode] = []
        self.items: ItemList = self.set_items()

    @abstractmethod
    def set_items(self) -> ItemList:
        """A method used to initialize or set the ItemList"""

    def set_parent(self, parent: PageDataNode):
        self.parent = parent

    def add_child(self, child: PageDataNode):
        child.set_parent(self)
        self.children.append(child)

    def get_parent(self) -> PageDataNode:
        return self.parent

    def get_child(self, find: Union[UUID, str]) -> PageDataNode:
        for child in self.children:
            if (isinstance(find, str) and child.name == find) or (isinstance(find, UUID) and child.id == find):
                return child

        raise ChildNotFound(find)

    @final
    def display(self) -> T:
        return self.__display(self.data)

    @staticmethod
    @abstractmethod
    def __display(data: D) -> T:
        """How the page should be displayed"""


class PageDataNodePromise(ABC, PageDataNode):

    def get_child(self, find: Union[UUID, str]) -> PageDataNode:
        child = super().get_child(find)
        return self.generate_children(child.data)

    @staticmethod
    @abstractmethod
    def generate_children(data: D) -> PageDataNode:
        """A method that generates the children of a PageDataNode and returns it"""
