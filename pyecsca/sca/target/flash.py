"""Provides a mix-in class of a flashable target (e.g. one where the code gets flashed to it before running)."""

from public import public
from abc import ABC, abstractmethod


@public
class Flashable(ABC):
    """A flashable target."""

    @abstractmethod
    def flash(self, fw_path: str) -> bool:
        """
        Flash the firmware at `fw_path` to the target.

        :param fw_path: The path to the firmware blob.
        :return: Whether the flashing was successful.
        """
        raise NotImplementedError
