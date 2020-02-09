from typing import Union

from chipwhisperer.capture.scopes import OpenADC
from chipwhisperer.capture.targets.simpleserial_readers.cw import SimpleSerial_ChipWhisperer
from chipwhisperer.capture.targets.simpleserial_readers.cwlite import SimpleSerial_ChipWhispererLite
from chipwhisperer.capture.targets.simpleserial_readers.sys_serial import SimpleSerial_serial
from public import public

from .serial import SerialTarget


@public
class SimpleSerialTarget(SerialTarget):  # pragma: no cover

    def __init__(self, ser: Union[
        SimpleSerial_ChipWhisperer, SimpleSerial_ChipWhispererLite, SimpleSerial_serial],
                 scope: OpenADC):
        super().__init__()
        self.ser = ser
        self.scope = scope

    def connect(self):
        self.ser.con(self.scope)

    def write(self, data: bytes):
        self.ser.write(data)
        self.ser.flush()

    def read(self, timeout: int) -> bytes:
        return self.ser.read(0, timeout)

    def disconnect(self):
        self.ser.dis()
