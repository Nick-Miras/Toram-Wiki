from abc import ABC, abstractmethod


class ContainerPaths(ABC):
    """Path of the container that contains the information card"""

    @staticmethod
    @abstractmethod
    def get() -> str:
        """returns xpath for the container"""


class CorynContainerPaths(ContainerPaths, ABC):
    """Container Path for https://coryn.club/"""


class ToramIDContainerPaths(ContainerPaths, ABC):
    """Container Path for https://toram-id.info/"""


class ItemPath(CorynContainerPaths):

    @staticmethod
    def get() -> str:
        return '//div[./div[@class="card-title"]]'


class MonsterPath(CorynContainerPaths):

    @staticmethod
    def get() -> str:
        return '//div[./div/div[@class="card-title-inverse"]]'


class SkillPath(CorynContainerPaths):

    @staticmethod
    def get() -> str:
        return '//div[./div/div/p[@class="card-title"]]'


class LevellingPath(CorynContainerPaths):

    @staticmethod
    def get() -> str:
        return '//div[@class="level-row"]'
