from public import public
from abc import ABC, abstractmethod


@public
class Flashable(ABC):
    """A flashable target."""

    @abstractmethod
    def flash(self, fw_path: str) -> bool:
        ...
