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
    data: Optional[bytes] = None
    ne: Optional[int] = None

    def __bytes__(self):
        if self.data is None or len(self.data) == 0:
            if self.ne is None or self.ne == 0:
                # Case 1
                return bytes([self.cls, self.ins, self.p1, self.p2])
            elif self.ne <= 256:
                # Case 2s
                return bytes([self.cls, self.ins, self.p1, self.p2, self.ne if self.ne != 256 else 0])
            else:
                # Case 2e
                return bytes([self.cls, self.ins, self.p1, self.p2]) + (self.ne.to_bytes(2, "big") if self.ne != 65536 else bytes([0, 0]))
        elif self.ne is None or self.ne == 0:
            if len(self.data) <= 255:
                # Case 3s
                return bytes([self.cls, self.ins, self.p1, self.p2, len(self.data)]) + self.data
            else:
                # Case 3e
                return bytes([self.cls, self.ins, self.p1, self.p2, 0]) + len(self.data).to_bytes(2, "big") + self.data
        else:
            if len(self.data) <= 255 and self.ne <= 256:
                # Case 4s
                return bytes([self.cls, self.ins, self.p1, self.p2, len(self.data)]) + self.data + bytes([self.ne if self.ne != 256 else 0])
            else:
                # Case 4e
                return bytes([self.cls, self.ins, self.p1, self.p2, 0]) + len(self.data).to_bytes(2, "big") + self.data + (self.ne.to_bytes(2, "big") if self.ne != 65536 else bytes([0, 0]))


@public
@dataclass
class ResponseAPDU(object):
    """A response APDU that can be received from an ISO7816-4 target."""
    data: bytes
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


@public
class ISO7816:
    SW_FILE_FULL = 0x6A84
    SW_UNKNOWN = 0x6F00
    SW_CLA_NOT_SUPPORTED = 0x6E00
    SW_INS_NOT_SUPPORTED = 0x6D00
    SW_CORRECT_LENGTH_00 = 0x6C00
    SW_WRONG_P1P2 = 0x6B00
    SW_INCORRECT_P1P2 = 0x6A86
    SW_RECORD_NOT_FOUND = 0x6A83
    SW_FILE_NOT_FOUND = 0x6A82
    SW_FUNC_NOT_SUPPORTED = 0x6A81
    SW_WRONG_DATA = 0x6A80
    SW_APPLET_SELECT_FAILED = 0x6999
    SW_COMMAND_NOT_ALLOWED = 0x6986
    SW_CONDITIONS_NOT_SATISFIED = 0x6985
    SW_DATA_INVALID = 0x6984
    SW_FILE_INVALID = 0x6983
    SW_SECURITY_STATUS_NOT_SATISFIED = 0x6982
    SW_WRONG_LENGTH = 0x6700
    SW_BYTES_REMAINING_00 = 0x6100
    SW_NO_ERROR = 0x9000
