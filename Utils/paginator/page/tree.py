from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
from uuid import UUID

from discord import ui

from . import display
from .models import TreeInformation
from ..exceptions import DisplayDataNotFound, ChildNotFound
from ...dataclasses.discord import ContentData

D = TypeVar('D')  # datatype of data


class PageDataTree(ABC, Generic[D]):
    __slots__ = "id", "name", "controller", "data", "parent", "_display_data", "children"

    def __init__(self, *, controller: PageTreeController, information: TreeInformation,
                 display_data: Optional[display.DisplayData] = None,
                 children: Optional[list[PageDataTree]] = None,
                 data: Optional[D] = None):
        self.id = information.id
        self.name = information.name
        self.controller = controller
        self.data: D = data
        self.parent: Optional[PageDataTree] = None
        self._display_data: Optional[display.DisplayData] = display_data

        self.children = []
        if children is not None:
            for child in children:
                self.add_child(child)

    def __eq__(self, other):
        return self.id == other.id

    def add_child(self, child: PageDataTree):
        child.set_parent(self)
        self.children.append(child)

    def set_parent(self, parent: PageDataTree):
        self.parent = parent

    def get_parent(self) -> PageDataTree:
        return self.parent

    def get_items(self) -> list[ui.Item]:
        if self._display_data is None or (display_data := self._display_data.items) is None:
            raise DisplayDataNotFound()
        return display_data(self).get_data()

    def get_content(self) -> ContentData:
        if self._display_data is None or (display_data := self._display_data.content) is None:
            raise DisplayDataNotFound()
        return display_data(self).get_data()

    @abstractmethod
    def initialize(self) -> None:
        """A method that is run when the :class:`PageTreeController` sets this as the current node"""

    @abstractmethod
    def get_child(self, find: UUID | str) -> PageDataTree:
        pass


class PageDataNode(PageDataTree, ABC, Generic[D]):

    def get_child(self, find: UUID | str) -> PageDataTree:
        for child in self.children:
            if (isinstance(find, UUID) and child.id == find) or (isinstance(find, str) and child.name == find):
                return child
        raise ChildNotFound(find)


class PageDataNodePromise(PageDataTree, ABC, Generic[D]):

    def get_child(self, find: UUID | str) -> PageDataTree:
        for child in self.children:
            if (isinstance(find, UUID) and child.id == find) or (isinstance(find, str) and child.name == find):
                return self.generate_children_of(child)
        raise ChildNotFound(find)

    @staticmethod
    @abstractmethod
    def generate_children_of(child: PageDataTree) -> PageDataTree:
        """A method that generates the children of a PageDataNode and returns it
        Args:
            child:
                PageDataTree without children
        """


class PageTreeController:
    __slots__ = "current", "view"

    def __init__(self):
        self.current: Optional[PageDataTree] = None

    def goto_parent(self):
        if (parent := self.current.get_parent()) is not None:
            if isinstance(self.current, PageDataNodePromise):
                self.current.children.clear()
            self.current = parent

    def goto_child(self, child):
        self.current = self.current.get_child(child)
        self.current.initialize()

    def goto_first_sibling(self):
        if self.current.parent is not None:
            parent_children: list[PageDataTree] = self.current.get_parent().children
            self.current = parent_children[0]

    def goto_last_sibling(self):
        if self.current.parent is not None:
            parent_children: list[PageDataTree] = self.current.get_parent().children
            self.current = parent_children[-1]

    def goto_next_sibling(self):
        if self.current.parent is not None:
            parent_children = self.current.get_parent().children
            current_index: int = parent_children.index(self.current)
            if (current_index + 1) < len(parent_children):  # if self.current is NOT the last item
                self.current = parent_children[current_index + 1]

    def goto_previous_sibling(self):
        if self.current.parent is not None:
            parent_children = self.current.get_parent().children
            current_index: int = parent_children.index(self.current)
            if current_index > 0:  # if self.current is NOT the first item
                self.current = parent_children[current_index - 1]
