from typing import Optional
from time import sleep

import chipwhisperer as cw
from chipwhisperer.capture.scopes.base import ScopeTemplate
from chipwhisperer.capture.targets import SimpleSerial
from public import public

from .flash import Flashable
from .simpleserial import SimpleSerialTarget


@public
class ChipWhispererTarget(Flashable, SimpleSerialTarget):  # pragma: no cover

    def __init__(self, target: SimpleSerial, scope: ScopeTemplate, programmer, **kwargs):
        super().__init__()
        self.target = target
        self.scope = scope
        self.programmer = programmer

    def connect(self):
        self.target.con(self.scope)
        self.target.baud = 115200
        sleep(0.5)

    def flash(self, fw_path: str) -> bool:
        try:
            cw.program_target(self.scope, self.programmer, fw_path)
        except Exception as e:
            print(e)
            return False
        return True

    def write(self, data: bytes):
        self.target.flush()
        self.target.write(data.decode())

    def read(self, num: int = 0, timeout: int = 0) -> bytes:
        return self.target.read(num, timeout).encode()

    def reset(self):
        self.scope.io.nrst = "low"
        sleep(0.05)
        self.scope.io.nrst = "high"
        sleep(0.05)

    def disconnect(self):
        self.target.dis()
