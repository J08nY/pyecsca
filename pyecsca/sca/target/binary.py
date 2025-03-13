"""Provides a binary target class which represents a target that is a runnable binary on the host."""

import subprocess
from subprocess import Popen
from typing import Optional, Union, List

from public import public

from pyecsca.sca.target.serial import SerialTarget


@public
class BinaryTarget(SerialTarget):
    """Binary target that is runnable on the host and communicates using the stdin/stdout streams."""

    binary: List[str]
    process: Optional[Popen] = None
    debug_output: bool

    def __init__(
        self, binary: Union[str, List[str]], debug_output: bool = False, **kwargs
    ):
        super().__init__()
        if not isinstance(binary, (str, list)):
            raise TypeError
        if isinstance(binary, str):
            binary = [binary]
        self.binary = binary
        self.debug_output = debug_output

    def connect(self):
        self.process = Popen(
            self.binary,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def write(self, data: bytes) -> None:
        if self.process is None:
            raise ValueError
        if self.debug_output:
            print(">>", data.decode())
        if self.process.stdin:
            self.process.stdin.write(data.decode())
            self.process.stdin.flush()

    def read(self, num: int = 0, timeout: int = 0) -> bytes:
        if self.process is None:
            raise ValueError
        if self.process.stdout:
            if num != 0:
                read = self.process.stdout.readline(num)
            else:
                read = self.process.stdout.readline()
        else:
            read = bytes()  # pragma: no cover
        if self.debug_output:
            print("<<", read, end="")
        return read.encode()

    def disconnect(self):
        if self.process is None:
            return
        if self.process.stdin is not None:
            self.process.stdin.close()
        if self.process.stdout is not None:
            self.process.stdout.close()
        self.process.terminate()
        self.process.wait()
