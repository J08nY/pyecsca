"""Provides a smartcard target communicating via PC/SC (Personal Computer/Smart Card)."""
from typing import Union, Optional

from public import public
from smartcard.CardConnection import CardConnection
from smartcard.System import readers
from smartcard.pcsc.PCSCCardConnection import PCSCCardConnection
from smartcard.pcsc.PCSCReader import PCSCReader

from pyecsca.sca.target.ISO7816 import ISO7816Target, CommandAPDU, ResponseAPDU, ISO7816, CardProtocol, \
    CardConnectionException


@public
class PCSCTarget(ISO7816Target):  # pragma: no cover
    """Smartcard target communicating via PCSC."""

    def __init__(self, reader: Union[str, PCSCReader]):
        if isinstance(reader, str):
            rs = readers()
            for r in rs:
                if r.name == reader:
                    self.reader = r
                    break
            else:
                raise ValueError(f"Reader '{reader}' not found.")
        else:
            self.reader = reader
        self.connection: PCSCCardConnection = self.reader.createConnection()

    def connect(self, protocol: Optional[CardProtocol] = None):
        proto = CardConnection.T0_protocol | CardConnection.T1_protocol
        if protocol == CardProtocol.T0:
            proto = CardConnection.T0_protocol
        elif protocol == CardProtocol.T1:
            proto = CardConnection.T1_protocol
        try:
            self.connection.connect(proto)
        except:  # noqa
            raise CardConnectionException()

    @property
    def atr(self) -> bytes:
        return bytes(self.connection.getATR())

    def select(self, aid: bytes) -> bool:
        apdu = CommandAPDU(0x00, 0xA4, 0x04, 0x00, aid)
        resp = self.send_apdu(apdu)
        return resp.sw == ISO7816.SW_NO_ERROR

    def send_apdu(self, apdu: CommandAPDU) -> ResponseAPDU:
        resp, sw1, sw2 = self.connection.transmit(list(bytes(apdu)))
        return ResponseAPDU(bytes(resp), sw1 << 8 | sw2)

    def disconnect(self):
        self.connection.disconnect()
