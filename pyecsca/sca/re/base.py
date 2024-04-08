from abc import abstractmethod, ABC
from typing import Optional, Any, Set

from public import public

from .tree import Tree


@public
class RE(ABC):
    tree: Optional[Tree] = None
    configs: Set[Any]

    def __init__(self, configs: Set[Any]):
        self.configs = configs

    @abstractmethod
    def build_tree(self, *args, **kwargs):
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
