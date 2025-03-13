"""Provides an abstract target class communicating using the `ChipWhisperer's <https://github.com/newaetech/chipwhisperer/>`_ SimpleSerial protocol."""

from abc import ABC
from time import time_ns, sleep
from typing import Mapping, Union

from public import public

from pyecsca.sca.target.serial import SerialTarget


@public
class SimpleSerialMessage:
    """A SimpleSerial message consisting of a starting character and a hexadecimal string."""

    char: str
    data: str

    def __init__(self, char: str, data: str):
        self.char = char
        self.data = data

    @staticmethod
    def from_raw(raw: Union[str, bytes]) -> "SimpleSerialMessage":
        if isinstance(raw, bytes):
            raw = raw.decode()
        return SimpleSerialMessage(raw[0], raw[1:])

    def __bytes__(self):
        return str(self).encode()

    def __str__(self):
        return self.char + self.data

    def __repr__(self):
        return str(self)


@public
class SimpleSerialTarget(SerialTarget, ABC):
    """A SimpleSerial-ish target, sends and receives SimpleSerial messages over a serial link."""

    def recv_msgs(self, timeout: int) -> Mapping[str, SimpleSerialMessage]:
        """
        Receive :py:class:`SimpleSerialMessage` messages, while waiting upto :paramref:`~.recv_msgs.timeout` seconds.

        :param timeout: How long to wait.
        :return: The received messages with their char.
        """
        start = time_ns() // 1000000
        buffer = bytes()
        # Expect "z00" confirmation response, as in SimpleSerial 1.
        while not buffer.endswith(b"z00\n"):
            wait = timeout - ((time_ns() // 1000000) - start)
            if wait <= 0:
                break
            buffer += self.read(1 if not buffer else 0, wait)
        if not buffer:
            return {}
        msgs = buffer.split(b"\n")
        if buffer.endswith(b"\n"):
            msgs.pop()

        result = {}
        for raw in msgs:
            msg = SimpleSerialMessage.from_raw(raw)
            result[msg.char] = msg
        return result

    def send_cmd(
        self, cmd: SimpleSerialMessage, timeout: int
    ) -> Mapping[str, SimpleSerialMessage]:
        """
        Send a :py:class:`SimpleSerialMessage` and receive the response messages that the command produces, within a :paramref:`~.send_cmd.timeout`.

        :param cmd: The command message to send.
        :param timeout: The timeout value to wait for the responses.
        :return: A mapping of the starting character of the message to the message.
        """
        data = bytes(cmd)
        for i in range(0, len(data), 64):
            chunk = data[i : i + 64]
            sleep(0.010)
            self.write(chunk)
        self.write(b"\n")
        return self.recv_msgs(timeout)
