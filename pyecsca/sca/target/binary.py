import subprocess
from subprocess import Popen
from typing import Optional

from public import public

from .serial import SerialTarget


@public
class BinaryTarget(SerialTarget):
    binary: str
    process: Optional[Popen]
    debug_output: bool

    def __init__(self, binary: str, debug_output: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.binary = binary
        self.debug_output = debug_output

    def connect(self):
        self.process = Popen([self.binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             text=True, bufsize=1)

    def write(self, data: bytes):
        if self.process is None:
            raise ValueError
        if self.debug_output:
            print(">>", data.decode())
        self.process.stdin.write(data.decode())
        self.process.stdin.flush()

    def read(self, num: Optional[int] = 0, timeout: Optional[int] = 0) -> bytes:
        if self.process is None:
            raise ValueError
        if num != 0:
            read = self.process.stdout.readline(num)
        else:
            read = self.process.stdout.readline()
        if self.debug_output:
            print("<<", read, end="")
        return read.encode()

    def disconnect(self):
        if self.process is None:
            return
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.terminate()
        self.process.wait()
