from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional

from public import public

from .base import Target


@public
@dataclass
class CommandAPDU(object):  # pragma: no cover
    """A command APDU that can be sent to an ISO7816-4 target."""
    cls: int
    ins: int
    p1: int
    p2: int
    data: Optional[bytes]

    def __bytes__(self):
        if self.data is None or len(self.data) == 0:
            return bytes([self.cls, self.ins, self.p1, self.p2])
        elif len(self.data) <= 255:
            return bytes([self.cls, self.ins, self.p1, self.p2, len(self.data)]) + self.data
        else:
            data_len = len(self.data)
            return bytes([self.cls, self.ins, self.p1, self.p2, 0, data_len >> 8,
                          data_len & 0xff]) + self.data


@public
@dataclass
class ResponseAPDU(object):
    """A response APDU that can be received from an ISO7816-4 target."""
    data: Optional[bytes]
    sw: int


@public
class ISO7816Target(Target, ABC):
    """An ISO7816-4 target."""

    @property
    @abstractmethod
    def atr(self) -> bytes:
        """The ATR (Answer To Reset) of the target."""
        ...

    @abstractmethod
    def select(self, aid: bytes) -> bool:
        """
        Select an applet with `aid`.

        :param aid: The AID of the applet to select.
        :return: Whether the selection was successful.
        """
        ...

    @abstractmethod
    def send_apdu(self, apdu: CommandAPDU) -> ResponseAPDU:
        """
        Send an APDU to the selected applet.

        :param apdu: The APDU to send.
        :return: The response.
        """
        ...
