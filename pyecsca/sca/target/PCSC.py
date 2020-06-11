from typing import Union

from public import public
from smartcard.CardConnection import CardConnection
from smartcard.System import readers
from smartcard.pcsc.PCSCCardConnection import PCSCCardConnection
from smartcard.pcsc.PCSCReader import PCSCReader

from .ISO7816 import ISO7816Target, CommandAPDU, ResponseAPDU, ISO7816


@public
class PCSCTarget(ISO7816Target):  # pragma: no cover
    """A smartcard target communicating via PCSC."""

    def __init__(self, reader: Union[str, PCSCReader]):
        if isinstance(reader, str):
            rs = readers()
            for r in rs:
                if r.name == reader:
                    self.reader = r
                    break
            else:
                raise ValueError("Reader '{}' not found.".format(reader))
        else:
            self.reader = reader
        self.connection: PCSCCardConnection = self.reader.createConnection()

    def connect(self):
        self.connection.connect(CardConnection.T0_protocol | CardConnection.T1_protocol)

    @property
    def atr(self) -> bytes:
        return bytes(self.connection.getATR())

    def select(self, aid: bytes) -> bool:
        apdu = CommandAPDU(0x00, 0xa4, 0x04, 0x00, aid)
        resp = self.send_apdu(apdu)
        return resp.sw == ISO7816.SW_NO_ERROR

    def send_apdu(self, apdu: CommandAPDU) -> ResponseAPDU:
        resp, sw1, sw2 = self.connection.transmit(list(bytes(apdu)))
        return ResponseAPDU(bytes(resp), sw1 << 8 | sw2)

    def disconnect(self):
        self.connection.disconnect()
