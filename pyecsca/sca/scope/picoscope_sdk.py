"""Provides an oscilloscope class for PicoScope branded oscilloscopes using the official `picosdk-python-wrappers <https://github.com/picotech/picosdk-python-wrappers>`_."""
import ctypes
from math import log2, floor
from time import time_ns, sleep
from typing import cast, Mapping, Optional, MutableMapping, Union, Tuple

import numpy as np
from picosdk.errors import CannotFindPicoSDKError
from picosdk.functions import assert_pico_ok
from picosdk.library import Library

try:
    from picosdk.ps3000 import ps3000
except CannotFindPicoSDKError as exc:
    ps3000 = exc
try:
    from picosdk.ps3000a import ps3000a
except CannotFindPicoSDKError as exc:
    ps3000a = exc
try:
    from picosdk.ps4000 import ps4000
except CannotFindPicoSDKError as exc:
    ps4000 = exc
try:
    from picosdk.ps5000 import ps5000
except CannotFindPicoSDKError as exc:
    ps5000 = exc
try:
    from picosdk.ps6000 import ps6000
except CannotFindPicoSDKError as exc:
    ps6000 = exc
from public import public

from pyecsca.sca.scope.base import Scope, SampleType
from pyecsca.sca.trace import Trace


def adc2volt(
        adc: Union[np.ndarray, ctypes.c_int16],
        volt_range: float,
        adc_minmax: int,
        dtype=np.float32,
) -> Union[np.ndarray, float]:  # pragma: no cover
    """
    Convert raw adc values to volts.

    :param adc: Either a single value (:py:class:`ctypes.c_int16`) or an array (:py:class:`np.ndarray`) of those to convert.
    :param volt_range: The voltage range used for collecting the samples.
    :param adc_minmax:
    :param dtype: The numpy ``dtype`` of the output.
    :return: The converted values.
    """
    if isinstance(adc, ctypes.c_int16):
        return (adc.value / adc_minmax) * volt_range
    if isinstance(adc, np.ndarray):
        return ((adc / adc_minmax) * volt_range).astype(dtype=dtype, copy=False)
    raise ValueError


def volt2adc(
        volt: Union[np.ndarray, float], volt_range: float, adc_minmax: int, dtype=np.float32
) -> Union[np.ndarray, ctypes.c_int16]:  # pragma: no cover
    """
    Convert volt values to raw adc values.

    :param volt: Either a single value (:py:class:`float`) or an array (:py:class:`np.ndarray`) of those to convert.
    :param volt_range: The voltage range used for collecting the samples.
    :param adc_minmax:
    :param dtype: The numpy ``dtype`` of the output.
    :return: The converted values.
    """
    if isinstance(volt, float):
        return ctypes.c_int16(int((volt / volt_range) * adc_minmax))
    if isinstance(volt, np.ndarray):
        return ((volt / volt_range) * adc_minmax).astype(dtype=dtype, copy=False)
    raise ValueError


@public
class PicoScopeSdk(Scope):  # pragma: no cover
    """PicoScope based scope."""

    MODULE: Library
    PREFIX: str
    CHANNELS: Mapping
    RANGES: Mapping
    MAX_ADC_VALUE: int
    MIN_ADC_VALUE: int
    COUPLING: Mapping
    TIME_UNITS: Mapping
    TRIGGERS: Mapping = {"above": 0, "below": 1, "rising": 2, "falling": 3}
    _variant: Optional[str]

    def __init__(self, variant: Optional[str] = None):
        super().__init__()
        self.handle: ctypes.c_int16 = ctypes.c_int16()
        self.frequency: Optional[int] = None
        self.pretrig: Optional[int] = None
        self.posttrig: Optional[int] = None
        self.samples: Optional[int] = None
        self.timebase: Optional[int] = None
        self.buffers: MutableMapping = {}
        self.ranges: MutableMapping = {}
        self._variant = variant

    def open(self) -> None:
        assert_pico_ok(self._dispatch_call("OpenUnit", ctypes.byref(self.handle)))

    @property
    def channels(self):
        return list(self.CHANNELS.keys())

    def get_variant(self):
        if self._variant is not None:
            return self._variant
        info = ctypes.create_string_buffer(6)
        size = ctypes.c_int16()
        assert_pico_ok(
            self._dispatch_call(
                "GetUnitInfo", self.handle, info, ctypes.c_int16(6), ctypes.byref(size), ctypes.c_uint(3)
            )
        )
        self._variant = "".join(chr(i) for i in info[: size.value - 1])  # type: ignore
        return self._variant

    def setup_frequency(
            self, frequency: int, pretrig: int, posttrig: int
    ) -> Tuple[int, int]:
        return self.set_frequency(frequency, pretrig, posttrig)

    def set_channel(
            self, channel: str, enabled: bool, coupling: str, range: float, offset: float
    ):
        if offset != 0.0:
            raise ValueError("Nonzero offset not supported.")
        if channel not in self.CHANNELS:
            raise ValueError(f"Channel {channel} not in available channels: {self.CHANNELS.keys()}")
        if coupling not in self.COUPLING:
            raise ValueError(f"Coupling {coupling} not in available couplings: {self.COUPLING.keys()}")
        if range not in self.RANGES:
            raise ValueError(f"Range {range} not in available ranges: {self.RANGES.keys()}")
        assert_pico_ok(
            self._dispatch_call(
                "SetChannel",
                self.handle,
                self.CHANNELS[channel],
                enabled,
                self.COUPLING[coupling],
                self.RANGES[range],
            )
        )
        self.ranges[channel] = range

    def setup_channel(
            self, channel: str, coupling: str, range: float, offset: float, enable: bool
    ):
        self.set_channel(channel, enable, coupling, range, offset)

    def _set_freq(
            self,
            frequency: int,
            pretrig: int,
            posttrig: int,
            period_bound: float,
            timebase_bound: int,
            low_freq: int,
            high_freq: int,
            high_subtract: int,
    ) -> Tuple[int, int]:
        samples = pretrig + posttrig
        period = 1 / frequency
        if low_freq == 0 or period > period_bound:
            tb = floor(high_freq / frequency + high_subtract)
            actual_frequency = high_freq // (tb - high_subtract)
        else:
            tb = min(floor(log2(low_freq) - log2(frequency)), timebase_bound)
            actual_frequency = low_freq // 2 ** tb
        max_samples = ctypes.c_int32()
        interval_nanoseconds = ctypes.c_int32()
        assert_pico_ok(
            self._dispatch_call(
                "GetTimebase",
                self.handle,
                tb,
                samples,
                ctypes.byref(interval_nanoseconds),
                0,
                ctypes.byref(max_samples),
                0
            )
        )
        if max_samples.value < samples:
            pretrig = max_samples.value * (pretrig // samples)
            posttrig = max_samples.value - pretrig
            samples = max_samples.value
        self.frequency = actual_frequency
        self.samples = samples
        self.pretrig = pretrig
        self.posttrig = posttrig
        self.timebase = tb
        return actual_frequency, samples

    def set_frequency(
            self, frequency: int, pretrig: int, posttrig: int
    ) -> Tuple[int, int]:
        raise NotImplementedError

    def setup_trigger(
            self,
            channel: str,
            threshold: float,
            direction: str,
            delay: int,
            timeout: int,
            enable: bool,
    ):
        self.set_trigger(direction, enable, threshold, channel, delay, timeout)

    def set_trigger(
            self,
            type: str,
            enabled: bool,
            value: float,
            channel: str,
            delay: int,
            timeout: int,
    ):
        assert_pico_ok(
            self._dispatch_call(
                "SetSimpleTrigger",
                self.handle,
                enabled,
                self.CHANNELS[channel],
                volt2adc(value, self.ranges[channel], self.MAX_ADC_VALUE),
                self.TRIGGERS[type],
                delay,
                timeout,
            )
        )

    def setup_capture(self, channel: str, enable: bool):
        self.set_buffer(channel, enable)

    def set_buffer(self, channel: str, enable: bool):
        if self.samples is None:
            raise ValueError
        if enable:
            if channel in self.buffers:
                del self.buffers[channel]
            buffer = (ctypes.c_int16 * self.samples)()
            assert_pico_ok(
                self._dispatch_call(
                    "SetDataBuffer",
                    self.handle,
                    self.CHANNELS[channel],
                    ctypes.byref(buffer),
                    self.samples,
                )
            )
            self.buffers[channel] = buffer
        else:
            assert_pico_ok(
                self._dispatch_call(
                    "SetDataBuffer",
                    self.handle,
                    self.CHANNELS[channel],
                    None,
                    self.samples,
                )
            )
            del self.buffers[channel]

    def arm(self):
        if self.samples is None or self.timebase is None:
            raise ValueError
        assert_pico_ok(
            self._dispatch_call(
                "RunBlock",
                self.handle,
                self.pretrig,
                self.posttrig,
                self.timebase,
                0,
                None,
                0,
                None,
                None,
            )
        )

    def capture(self, timeout: Optional[int] = None) -> bool:
        start = time_ns()
        if self.samples is None:
            raise ValueError
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            sleep(0.001)
            assert_pico_ok(
                self._dispatch_call("IsReady", self.handle, ctypes.byref(ready))
            )
            if timeout is not None and (time_ns() - start) / 1e6 >= timeout:
                return False
        return True

    def retrieve(
            self, channel: str, type: SampleType, dtype=np.float32
    ) -> Optional[Trace]:
        if self.samples is None:
            raise ValueError
        actual_samples = ctypes.c_int32(self.samples)
        overflow = ctypes.c_int16()
        assert_pico_ok(
            self._dispatch_call(
                "GetValues",
                self.handle,
                0,
                ctypes.byref(actual_samples),
                1,
                0,
                0,
                ctypes.byref(overflow),
            )
        )
        arr = np.array(self.buffers[channel], dtype=dtype)
        if type == SampleType.Raw:
            data = arr
        else:
            data = cast(
                np.ndarray,
                adc2volt(arr, self.ranges[channel], self.MAX_ADC_VALUE, dtype=dtype),
            )
        return Trace(
            data,
            {
                "sampling_frequency": self.frequency,
                "channel": channel,
                "sample_type": type,
            },
        )

    def stop(self):
        assert_pico_ok(self._dispatch_call("Stop"))

    def close(self):
        assert_pico_ok(self._dispatch_call("CloseUnit", self.handle))

    def _dispatch_call(self, name, *args, **kwargs):
        """
        A unit-generic call of a picoscope SDK method.
        """
        method = getattr(self.MODULE, self.PREFIX + name)
        if method is None:
            raise ValueError
        return method(*args, **kwargs)


if isinstance(ps3000, CannotFindPicoSDKError):

    @public
    class PS3000Scope(PicoScopeSdk):  # noqa, pragma: no cover, skipcq
        """PicoScope 3000 series oscilloscope is not available (Install `libps3000`)."""

        def __init__(self, variant: Optional[str] = None):
            super().__init__(variant)
            raise ps3000


else:  # pragma: no cover

    @public
    class PS3000Scope(PicoScopeSdk):  # type: ignore
        """PicoScope 3000 series oscilloscope."""

        MODULE = ps3000
        PREFIX = "ps3000"
        CHANNELS = {
            "A": ps3000.PS3000_CHANNEL["PS3000_CHANNEL_A"],
            "B": ps3000.PS3000_CHANNEL["PS3000_CHANNEL_B"],
            "C": ps3000.PS3000_CHANNEL["PS3000_CHANNEL_C"],
            "D": ps3000.PS3000_CHANNEL["PS3000_CHANNEL_D"],
        }

        RANGES = {
            0.02: ps3000.PS3000_VOLTAGE_RANGE["PS3000_20MV"],
            0.05: ps3000.PS3000_VOLTAGE_RANGE["PS3000_50MV"],
            0.10: ps3000.PS3000_VOLTAGE_RANGE["PS3000_100MV"],
            0.20: ps3000.PS3000_VOLTAGE_RANGE["PS3000_200MV"],
            0.50: ps3000.PS3000_VOLTAGE_RANGE["PS3000_500MV"],
            1.00: ps3000.PS3000_VOLTAGE_RANGE["PS3000_1V"],
            2.00: ps3000.PS3000_VOLTAGE_RANGE["PS3000_2V"],
            5.00: ps3000.PS3000_VOLTAGE_RANGE["PS3000_5V"],
            10.0: ps3000.PS3000_VOLTAGE_RANGE["PS3000_10V"],
            20.0: ps3000.PS3000_VOLTAGE_RANGE["PS3000_20V"],
            50.0: ps3000.PS3000_VOLTAGE_RANGE["PS3000_50V"],
            100.0: ps3000.PS3000_VOLTAGE_RANGE["PS3000_100V"],
            200.0: ps3000.PS3000_VOLTAGE_RANGE["PS3000_200V"],
            400.0: ps3000.PS3000_VOLTAGE_RANGE["PS3000_400V"],
        }

        MAX_ADC_VALUE = 32767
        MIN_ADC_VALUE = -32767

        COUPLING = {"AC": ps3000.PICO_COUPLING["AC"], "DC": ps3000.PICO_COUPLING["DC"]}

        def open(self) -> None:
            assert_pico_ok(self._dispatch_call("_open_unit"))  # , ctypes.byref(self.handle)

        def stop(self):
            assert_pico_ok(self._dispatch_call("_stop"))

        def close(self):
            assert_pico_ok(self._dispatch_call("_close_unit", self.handle))

        def get_variant(self):
            if self._variant is not None:
                return self._variant
            info = ctypes.create_string_buffer(6)
            size = ctypes.c_int16(6)
            info_variant = ctypes.c_int16(3)
            assert_pico_ok(
                self._dispatch_call(
                    "_get_unit_info", self.handle, info, size, info_variant
                )
            )
            self._variant = "".join(chr(i) for i in info[: size.value - 1])  # type: ignore
            return self._variant

        def set_frequency(
                self, frequency: int, pretrig: int, posttrig: int
        ):  # TODO: fix
            raise NotImplementedError

if isinstance(ps3000a, CannotFindPicoSDKError):

    @public
    class PS3000aScope(PicoScopeSdk):  # noqa, pragma: no cover, skipcq
        """PicoScope 3000 series (A API) oscilloscope is not available (Install `libps3000a`)."""

        def __init__(self, variant: Optional[str] = None):
            super().__init__(variant)
            raise ps3000a


else:  # pragma: no cover

    @public
    class PS3000aScope(PicoScopeSdk):  # type: ignore
        """PicoScope 3000 series oscilloscope (A API)."""

        MODULE = ps3000a
        PREFIX = "ps3000a"
        CHANNELS = {
            "A": ps3000a.PS3000A_CHANNEL["PS3000A_CHANNEL_A"],
            "B": ps3000a.PS3000A_CHANNEL["PS3000A_CHANNEL_B"],
            "C": ps3000a.PS3000A_CHANNEL["PS3000A_CHANNEL_C"],
            "D": ps3000a.PS3000A_CHANNEL["PS3000A_CHANNEL_D"],
        }

        RANGES = {
            0.01: ps3000a.PS3000A_RANGE["PS3000A_10MV"],
            0.02: ps3000a.PS3000A_RANGE["PS3000A_20MV"],
            0.05: ps3000a.PS3000A_RANGE["PS3000A_50MV"],
            0.10: ps3000a.PS3000A_RANGE["PS3000A_100MV"],
            0.20: ps3000a.PS3000A_RANGE["PS3000A_200MV"],
            0.50: ps3000a.PS3000A_RANGE["PS3000A_500MV"],
            1.00: ps3000a.PS3000A_RANGE["PS3000A_1V"],
            2.00: ps3000a.PS3000A_RANGE["PS3000A_2V"],
            5.00: ps3000a.PS3000A_RANGE["PS3000A_5V"],
            10.0: ps3000a.PS3000A_RANGE["PS3000A_10V"],
            20.0: ps3000a.PS3000A_RANGE["PS3000A_20V"],
            50.0: ps3000a.PS3000A_RANGE["PS3000A_50V"]
        }

        MAX_ADC_VALUE = 32767
        MIN_ADC_VALUE = -32767

        COUPLING = {"AC": ps3000a.PICO_COUPLING["AC"], "DC": ps3000a.PICO_COUPLING["DC"]}

        def open(self) -> None:
            assert_pico_ok(ps3000a.ps3000aOpenUnit(ctypes.byref(self.handle), None))

        def set_channel(
                self,
                channel: str,
                enabled: bool,
                coupling: str,
                range: float,
                offset: float,
        ):
            if channel not in self.CHANNELS:
                raise ValueError(f"Channel {channel} not in available channels: {self.CHANNELS.keys()}")
            if coupling not in self.COUPLING:
                raise ValueError(f"Coupling {coupling} not in available couplings: {self.COUPLING.keys()}")
            if range not in self.RANGES:
                raise ValueError(f"Range {range} not in available ranges: {self.RANGES.keys()}")
            assert_pico_ok(
                ps3000a.ps3000aSetChannel(
                    self.handle,
                    self.CHANNELS[channel],
                    enabled,
                    self.COUPLING[coupling],
                    self.RANGES[range],
                    offset
                )
            )
            self.ranges[channel] = range

        def set_buffer(self, channel: str, enable: bool):
            if self.samples is None:
                raise ValueError
            if enable:
                if channel in self.buffers:
                    del self.buffers[channel]
                buffer = (ctypes.c_int16 * self.samples)()
                assert_pico_ok(
                    ps3000a.ps3000aSetDataBuffer(
                        self.handle,
                        self.CHANNELS[channel],
                        ctypes.byref(buffer),
                        self.samples,
                        0,
                        ps3000a.PS3000A_RATIO_MODE["PS3000A_RATIO_MODE_NONE"]
                    )
                )
                self.buffers[channel] = buffer
            else:
                assert_pico_ok(
                    ps3000a.ps3000aSetDataBuffer(
                        self.handle, self.CHANNELS[channel], None, self.samples, 0,
                        ps3000a.PS3000A_RATIO_MODE["PS3000A_RATIO_MODE_NONE"]
                    )
                )
                del self.buffers[channel]

        def set_frequency(self, frequency: int, pretrig: int, posttrig: int):
            variant = self.get_variant()
            if variant in ("3000A", "3000B"):
                # This only holds for the 2-channel versions
                # 4-channel versions have the settings from branch "D".
                return self._set_freq(frequency, pretrig, posttrig, 8e-9, 2, 500_000_000, 62_500_000, 2)
            elif variant == "3000":
                return self._set_freq(frequency, pretrig, posttrig, 4e-9, 1, 500_000_000, 125_000_000, 1)
            elif variant.endswith("D"):
                return self._set_freq(frequency, pretrig, posttrig, 4e-9, 2, 1_000_000_000, 125_000_000, 2)
            # TODO: Needs more per-device settings to be generic.

if isinstance(ps4000, CannotFindPicoSDKError):

    @public
    class PS4000Scope(PicoScopeSdk):  # noqa, pragma: no cover, skipcq
        """PicoScope 4000 series oscilloscope is not available (Install `libps4000`)."""

        def __init__(self, variant: Optional[str] = None):
            super().__init__(variant)
            raise ps4000


else:  # pragma: no cover

    @public
    class PS4000Scope(PicoScopeSdk):  # type: ignore
        """PicoScope 4000 series oscilloscope."""

        MODULE = ps4000
        PREFIX = "ps4000"
        CHANNELS = {
            "A": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_A"],
            "B": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_B"],
            "C": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_C"],
            "D": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_D"],
        }

        RANGES = {
            0.01: ps4000.PS4000_RANGE["PS4000_10MV"],
            0.02: ps4000.PS4000_RANGE["PS4000_20MV"],
            0.05: ps4000.PS4000_RANGE["PS4000_50MV"],
            0.10: ps4000.PS4000_RANGE["PS4000_100MV"],
            0.20: ps4000.PS4000_RANGE["PS4000_200MV"],
            0.50: ps4000.PS4000_RANGE["PS4000_500MV"],
            1.00: ps4000.PS4000_RANGE["PS4000_1V"],
            2.00: ps4000.PS4000_RANGE["PS4000_2V"],
            5.00: ps4000.PS4000_RANGE["PS4000_5V"],
            10.0: ps4000.PS4000_RANGE["PS4000_10V"],
            20.0: ps4000.PS4000_RANGE["PS4000_20V"],
            50.0: ps4000.PS4000_RANGE["PS4000_50V"],
            100.0: ps4000.PS4000_RANGE["PS4000_100V"],
        }

        MAX_ADC_VALUE = 32764
        MIN_ADC_VALUE = -32764

        COUPLING = {"AC": ps4000.PICO_COUPLING["AC"], "DC": ps4000.PICO_COUPLING["DC"]}

        def set_frequency(self, frequency: int, pretrig: int, posttrig: int):
            variant = self.get_variant()
            if variant in ("4223", "4224", "4423", "4424"):
                return self._set_freq(
                    frequency, pretrig, posttrig, 50e-9, 2, 80_000_000, 20_000_000, 1
                )
            elif variant in ("4226", "4227"):
                return self._set_freq(
                    frequency, pretrig, posttrig, 32e-9, 3, 250_000_000, 31_250_000, 2
                )
            elif variant == "4262":
                return self._set_freq(
                    frequency, pretrig, posttrig, 0, 0, 0, 10_000_000, -1
                )
            else:
                raise ValueError(f"Unknown variant: {variant}")

if isinstance(ps5000, CannotFindPicoSDKError):

    @public
    class PS5000Scope(PicoScopeSdk):  # noqa, pragma: no cover, skipcq
        """PicoScope 5000 series oscilloscope is not available (Install `libps5000`)."""

        def __init__(self, variant: Optional[str] = None):
            super().__init__(variant)
            raise ps5000


else:  # pragma: no cover

    @public
    class PS5000Scope(PicoScopeSdk):  # type: ignore
        """PicoScope 5000 series oscilloscope."""

        MODULE = ps5000
        PREFIX = "ps5000"
        CHANNELS = {
            "A": ps5000.PS5000_CHANNEL["PS5000_CHANNEL_A"],
            "B": ps5000.PS5000_CHANNEL["PS5000_CHANNEL_B"],
            "C": ps5000.PS5000_CHANNEL["PS5000_CHANNEL_C"],
            "D": ps5000.PS5000_CHANNEL["PS5000_CHANNEL_D"],
        }

        RANGES = {
            0.01: ps5000.PS5000_RANGE["PS5000_10MV"],
            0.02: ps5000.PS5000_RANGE["PS5000_20MV"],
            0.05: ps5000.PS5000_RANGE["PS5000_50MV"],
            0.10: ps5000.PS5000_RANGE["PS5000_100MV"],
            0.20: ps5000.PS5000_RANGE["PS5000_200MV"],
            0.50: ps5000.PS5000_RANGE["PS5000_500MV"],
            1.00: ps5000.PS5000_RANGE["PS5000_1V"],
            2.00: ps5000.PS5000_RANGE["PS5000_2V"],
            5.00: ps5000.PS5000_RANGE["PS5000_5V"],
            10.0: ps5000.PS5000_RANGE["PS5000_10V"],
            20.0: ps5000.PS5000_RANGE["PS5000_20V"],
            50.0: ps5000.PS5000_RANGE["PS5000_50V"],
        }

        MAX_ADC_VALUE = 32512
        MIN_ADC_VALUE = -32512

        COUPLING = {"AC": 0, "DC": 1}

        def set_frequency(self, frequency: int, pretrig: int, posttrig: int):
            return self._set_freq(
                frequency, pretrig, posttrig, 4e-9, 2, 1_000_000_000, 125_000_000, 2
            )

if isinstance(ps6000, CannotFindPicoSDKError):

    @public
    class PS6000Scope(PicoScopeSdk):  # noqa, pragma: no cover, skipcq
        """PicoScope 6000 series oscilloscope is not available (Install `libps6000`)."""

        def __init__(self, variant: Optional[str] = None):
            super().__init__(variant)
            raise ps6000


else:  # pragma: no cover

    @public
    class PS6000Scope(PicoScopeSdk):  # type: ignore
        """PicoScope 6000 series oscilloscope."""

        MODULE = ps6000
        PREFIX = "ps6000"
        CHANNELS = {
            "A": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_A"],
            "B": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_B"],
            "C": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_C"],
            "D": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_D"],
        }

        RANGES = {
            0.01: ps6000.PS6000_RANGE["PS6000A_10MV"],
            0.02: ps6000.PS6000_RANGE["PS6000_20MV"],
            0.05: ps6000.PS6000_RANGE["PS6000_50MV"],
            0.10: ps6000.PS6000_RANGE["PS6000_100MV"],
            0.20: ps6000.PS6000_RANGE["PS6000_200MV"],
            0.50: ps6000.PS6000_RANGE["PS6000_500MV"],
            1.00: ps6000.PS6000_RANGE["PS6000_1V"],
            2.00: ps6000.PS6000_RANGE["PS6000_2V"],
            5.00: ps6000.PS6000_RANGE["PS6000_5V"],
            10.0: ps6000.PS6000_RANGE["PS6000_10V"],
            20.0: ps6000.PS6000_RANGE["PS6000_20V"],
            50.0: ps6000.PS6000_RANGE["PS6000_50V"],
        }

        MAX_ADC_VALUE = 32512
        MIN_ADC_VALUE = -32512

        COUPLING = {
            "AC": ps6000.PS6000_COUPLING["PS6000_AC"],
            "DC": ps6000.PS6000_COUPLING["PS6000_DC_1M"],
            "DC_50": ps6000.PS6000_COUPLING["PS6000_DC_50R"],
        }

        def open(self):
            assert_pico_ok(ps6000.ps6000OpenUnit(ctypes.byref(self.handle), None))

        def set_channel(
                self,
                channel: str,
                enabled: bool,
                coupling: str,
                range: float,
                offset: float,
        ):
            if channel not in self.CHANNELS:
                raise ValueError(f"Channel {channel} not in available channels: {self.CHANNELS.keys()}")
            if coupling not in self.COUPLING:
                raise ValueError(f"Coupling {coupling} not in available couplings: {self.COUPLING.keys()}")
            if range not in self.RANGES:
                raise ValueError(f"Range {range} not in available ranges: {self.RANGES.keys()}")
            assert_pico_ok(
                ps6000.ps6000SetChannel(
                    self.handle,
                    self.CHANNELS[channel],
                    enabled,
                    self.COUPLING[coupling],
                    self.RANGES[range],
                    offset,
                    ps6000.PS6000_BANDWIDTH_LIMITER["PS6000_BW_FULL"],
                )
            )
            self.ranges[channel] = range

        def set_buffer(self, channel: str, enable: bool):
            if self.samples is None:
                raise ValueError
            if enable:
                if channel in self.buffers:
                    del self.buffers[channel]
                buffer = (ctypes.c_int16 * self.samples)()
                assert_pico_ok(
                    ps6000.ps6000SetDataBuffer(
                        self.handle,
                        self.CHANNELS[channel],
                        ctypes.byref(buffer),
                        self.samples,
                        0,
                    )
                )
                self.buffers[channel] = buffer
            else:
                assert_pico_ok(
                    ps6000.ps6000SetDataBuffer(
                        self.handle, self.CHANNELS[channel], None, self.samples, 0
                    )
                )
                del self.buffers[channel]

        def set_frequency(self, frequency: int, pretrig: int, posttrig: int):
            return self._set_freq(
                frequency, pretrig, posttrig, 3.2e-9, 4, 5_000_000_000, 156_250_000, 4
            )
