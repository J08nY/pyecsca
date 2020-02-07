import numpy as np
import struct
from enum import IntEnum
from io import BytesIO, RawIOBase, BufferedIOBase, UnsupportedOperation
from pathlib import Path
from public import public
from typing import Union, Optional, BinaryIO, List

from .base import TraceSet
from ..trace import Trace


@public
class SampleCoding(IntEnum):
    Int8 = 0x01
    Int16 = 0x02
    Int32 = 0x04
    Float8 = 0x11
    Float16 = 0x12
    Float32 = 0x14

    def dtype(self):
        char = "f" if self.value & 0x10 else "i"
        return np.dtype("<{}{}".format(char, self.value & 0x0f))


@public
class Parsers(object):
    @staticmethod
    def read_int(bytes):
        return int.from_bytes(bytes, byteorder="little")

    @staticmethod
    def read_bool(bytes):
        return Parsers.read_int(bytes) == 1

    @staticmethod
    def read_float(bytes):
        return struct.unpack("<f", bytes)[0]

    @staticmethod
    def read_str(bytes):
        return bytes.decode("ascii")

    @staticmethod
    def write_int(i, length=1):
        return int.to_bytes(i, length=length, byteorder="little")

    @staticmethod
    def write_bool(b, length=1):
        return Parsers.write_int(b, length=length)

    @staticmethod
    def write_float(f, length=None):
        return struct.pack("<{}".format("e" if length == 2 else "f"), f)

    @staticmethod
    def write_str(s, length=None):
        return s.encode("ascii")


@public
class InspectorTraceSet(TraceSet):
    """Riscure Inspector trace set format (.trs)."""

    num_traces: int
    num_samples: int
    sample_coding: SampleCoding
    data_space: int = 0
    title_space: int = 0

    global_title: str = "title"
    description: Optional[str] = None

    x_offset: int = 0
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_scale: float = 1
    y_scale: float = 1

    trace_offset: int = 0
    log_scale: int = 0

    scope_range: float = 0
    scope_coupling: int = 0
    scope_offset: float = 0
    scope_impedance: float = 0
    scope_id: Optional[str] = None

    filter_type: int = 0
    filter_frequency: float = 0
    filter_range: float = 0

    external_clock: bool = False
    external_clock_threshold: float = 0
    external_clock_multiplier: int = 0
    external_clock_phase_shift: int = 0
    external_clock_resampler_mask: int = 0
    external_clock_resampler_enabled: bool = False
    external_clock_frequencty: float = 0
    external_clock_time_base: int = 0

    _raw_traces: Optional[List[Trace]] = None
    _tag_parsers: dict = {
        0x41: ("num_traces", 4, Parsers.read_int, Parsers.write_int),
        0x42: ("num_samples", 4, Parsers.read_int, Parsers.write_int),
        0x43: ("sample_coding", 1,
               lambda bytes: SampleCoding(Parsers.read_int(bytes)),
               lambda coding, length: Parsers.write_int(coding.value,
                                                        length=length)),
        0x44: ("data_space", 2, Parsers.read_int, Parsers.write_int),
        0x45: ("title_space", 1, Parsers.read_int, Parsers.write_int),
        0x46: ("global_title", None, Parsers.read_str, Parsers.write_str),
        0x47: ("description", None, Parsers.read_str, Parsers.write_str),
        0x48: ("x_offset", None, Parsers.read_int, Parsers.write_int),
        0x49: ("x_label", None, Parsers.read_str, Parsers.write_str),
        0x4a: ("y_label", None, Parsers.read_str, Parsers.write_str),
        0x4b: ("x_scale", 4, Parsers.read_float, Parsers.write_float),
        0x4c: ("y_scale", 4, Parsers.read_float, Parsers.write_float),
        0x4d: ("trace_offset", 4, Parsers.read_int, Parsers.write_int),
        0x4e: ("log_scale", 1, Parsers.read_int, Parsers.write_int),
        0x55: ("scope_range", 4, Parsers.read_float, Parsers.write_float),
        0x56: ("scope_coupling", 4, Parsers.read_int, Parsers.write_int),
        0x57: ("scope_offset", 4, Parsers.read_float, Parsers.write_float),
        0x58: ("scope_impedance", 4, Parsers.read_float, Parsers.write_float),
        0x59: ("scope_id", None, Parsers.read_str, Parsers.write_str),
        0x5a: ("filter_type", 4, Parsers.read_int, Parsers.write_int),
        0x5b: ("filter_frequency", 4, Parsers.read_float, Parsers.write_float),
        0x5c: ("filter_range", 4, Parsers.read_float, Parsers.read_float),
        0x60: ("external_clock", 1, Parsers.read_bool, Parsers.write_bool),
        0x61: ("external_clock_threshold", 4, Parsers.read_float, Parsers.write_float),
        0x62: ("external_clock_multiplier", 4, Parsers.read_int, Parsers.write_int),
        0x63: ("external_clock_phase_shift", 4, Parsers.read_int, Parsers.write_int),
        0x64: ("external_clock_resampler_mask", 4, Parsers.read_int, Parsers.write_int),
        0x65: ("external_clock_resampler_enabled", 1, Parsers.read_bool, Parsers.write_bool),
        0x66: ("external_clock_frequency", 4, Parsers.read_float, Parsers.write_float),
        0x67: ("external_clock_time_base", 4, Parsers.read_int, Parsers.write_int)
    }
    _set_tags: set = set()

    def __init__(self, input: Optional[Union[str, Path, bytes, RawIOBase, BufferedIOBase]] = None,
                 keep_raw_traces: bool = True):
        """
        Read Inspector trace set from file path, bytes or file-like object.

        :param input: Input file path, bytes or file-like object.
        :param keep_raw_traces: Whether to store the raw (unscaled) traces as well.
        """
        traces = None
        if isinstance(input, bytes):
            with BytesIO(input) as f:
                traces = self.__read(f)
        elif isinstance(input, (Path, str)):
            with open(input, "rb") as r:
                traces = self.__read(r)
        elif isinstance(input, (RawIOBase, BufferedIOBase)):
            traces = self.__read(input)
        elif input is not None:
            raise ValueError(
                    "Cannot parse data, unknown input: {}".format(input))
        if traces is not None:
            super().__init__(*self.__scale(traces))
        else:
            super().__init__()
        if keep_raw_traces:
            self._raw_traces = traces
        else:
            del traces

    def __read(self, file):
        self._set_tags = set()
        while True:
            tag = ord(file.read(1))
            length = ord(file.read(1))
            if length & 0x80:
                length = Parsers.read_int(file.read(length & 0x7f))
            value = file.read(length)
            if tag in InspectorTraceSet._tag_parsers:
                tag_name, tag_len, tag_reader, _ = \
                    InspectorTraceSet._tag_parsers[tag]
                if tag_len is None or length == tag_len:
                    setattr(self, tag_name, tag_reader(value))
                    self._set_tags.add(tag)
            elif tag == 0x5f and length == 0:
                break
            else:
                continue
        result = []
        for _ in range(self.num_traces):
            title = None if self.title_space == 0 else Parsers.read_str(
                    file.read(self.title_space))
            data = None if self.data_space == 0 else file.read(self.data_space)
            dtype = self.sample_coding.dtype()
            try:
                samples = np.fromfile(file, dtype, self.num_samples)
            except UnsupportedOperation:
                samples = np.frombuffer(
                        file.read(dtype.itemsize * self.num_samples), dtype,
                        self.num_samples)
            result.append(Trace(title, data, samples, trace_set=self))
        return result

    def __write(self, file):
        for set_tag in self._set_tags:
            tag_name, tag_len, _, tag_writer = InspectorTraceSet._tag_parsers[
                set_tag]
            tag_byte = Parsers.write_int(set_tag, length=1)
            value_bytes = tag_writer(getattr(self, tag_name), tag_len)
            length = len(value_bytes)
            if length <= 0x7f:
                length_bytes = Parsers.write_int(length, length=1)
            else:
                length_data = Parsers.write_int(length, length=(length.bit_length() + 7) // 8)
                length_bytes = Parsers.write_int(
                        0x80 | len(length_data)) + length_data
            file.write(tag_byte)
            file.write(length_bytes)
            file.write(value_bytes)
        file.write(b"\x5f\x00")

        for trace in self._raw_traces:
            if self.title_space != 0 and trace.title is not None:
                file.write(Parsers.write_str(trace.title))
            if self.data_space != 0 and trace.data is not None:
                file.write(trace.data)
            try:
                trace.samples.tofile(file)
            except UnsupportedOperation:
                file.write(trace.samples.tobytes())

    def __scale(self, traces):
        return list(map(lambda trace: Trace(trace.title, trace.data,
                                            trace.samples.astype("f4") * self.y_scale,
                                            trace_set=self),
                        traces))

    def save(self, output: Union[Path, str, BinaryIO]):
        """
        Save this trace set into a file.

        :param output: An output path or file-like object.
        """
        if isinstance(output, (Path, str)):
            with open(output, "wb") as f:
                self.__write(f)
        elif isinstance(output, (RawIOBase, BufferedIOBase)):
            self.__write(output)
        else:
            raise ValueError("Cannot save data, unknown output: {}".format(output))

    def __bytes__(self):
        """Return the byte-representation of this trace set file."""
        with BytesIO() as b:
            self.save(b)
            return b.getvalue()

    @property
    def raw(self) -> Optional[List[Trace]]:
        """The raw (unscaled) traces, as read from the trace set file."""
        if self._raw_traces is None:
            return None
        return list(self._raw_traces)

    @property
    def sampling_frequency(self) -> int:
        """The sampling frequency of the trace set."""
        return int(1 / self.x_scale)

    def __repr__(self):
        args = ", ".join(
                [f"{self._tag_parsers[set_tag][0]}={getattr(self, self._tag_parsers[set_tag][0])!r}"
                 for set_tag in self._set_tags])
        return f"InspectorTraceSet({args})"
