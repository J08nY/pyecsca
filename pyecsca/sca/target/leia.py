"""Provides a smartcard target communicating via the LEIA board in solo mode."""
from typing import Optional

from smartleia import LEIA, create_APDU_from_bytes, T

from pyecsca.sca.target.ISO7816 import ISO7816Target, CommandAPDU, ResponseAPDU, ISO7816, CardProtocol, \
    CardConnectionException


class LEIATarget(ISO7816Target):  # pragma: no cover
    """Smartcard target communicating via LEIA in solo mode."""

    def __init__(self, leia: LEIA):
        self.leia = leia

    @property
    def atr(self) -> bytes:
        return self.leia.get_ATR().normalized()

    @property
    def card_present(self) -> bool:
        return self.leia.is_card_inserted()

    def select(self, aid: bytes) -> bool:
        apdu = CommandAPDU(0x00, 0xA4, 0x04, 0x00, aid)
        resp = self.send_apdu(apdu)
        return resp.sw == ISO7816.SW_NO_ERROR

    def send_apdu(self, apdu: CommandAPDU) -> ResponseAPDU:
        leia_apdu = create_APDU_from_bytes(bytes(apdu))
        resp = self.leia.send_APDU(leia_apdu)
        return ResponseAPDU(resp.data, resp.sw1 << 8 | resp.sw2)

    def connect(self, protocol: Optional[CardProtocol] = None):
        proto = T.AUTO
        if protocol == CardProtocol.T0:
            proto = T.T0
        elif protocol == CardProtocol.T1:
            proto = T.T1
        try:
            self.leia.configure_smartcard(protocol_to_use=proto)
        except:  # noqa
            raise CardConnectionException()

    def disconnect(self):
        pass
