from abc import abstractmethod, ABC
from typing import Optional, Any, Set

from public import public

from pyecsca.sca.re.tree import Tree


@public
class RE(ABC):
    """A base class for Reverse-Engineering methods."""

    tree: Optional[Tree] = None
    """The RE tree (if any)."""
    configs: Set[Any]
    """The set of configurations to reverse-engineer."""

    def __init__(self, configs: Set[Any]):
        self.configs = configs

    @abstractmethod
    def build_tree(self, *args, **kwargs):
        """Build the RE tree."""
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        """Run the reverse-engineering (and obtain a result set of possible configurations)."""
        pass
