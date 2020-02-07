import ctypes
from time import time_ns, sleep
from math import log2, floor
from typing import Mapping, Optional, MutableMapping, Union, Tuple

import numpy as np
from picosdk.functions import assert_pico_ok
from picosdk.library import Library
from picosdk.ps4000 import ps4000
from picosdk.ps6000 import ps6000
from public import public

from .base import Scope


def adc2volt(adc: Union[np.ndarray, ctypes.c_int16],
             volt_range: float, adc_minmax: int) -> Union[np.ndarray, float]:  # pragma: no cover
    if isinstance(adc, ctypes.c_int16):
        adc = adc.value
    return (adc / adc_minmax) * volt_range


def volt2adc(volt: Union[np.ndarray, float],
             volt_range: float, adc_minmax: int) -> Union[
    np.ndarray, ctypes.c_int16]:  # pragma: no cover
    if isinstance(volt, float):
        return ctypes.c_int16(int((volt / volt_range) * adc_minmax))
    return (volt / volt_range) * adc_minmax


@public
class PicoScopeSdk(Scope):  # pragma: no cover
    """A PicoScope based scope."""
    MODULE: Library
    PREFIX: str
    CHANNELS: Mapping
    RANGES: Mapping
    MAX_ADC_VALUE: int
    MIN_ADC_VALUE: int
    COUPLING: Mapping
    TIME_UNITS: Mapping
    TRIGGERS: Mapping = {
        "above": 0,
        "below": 1,
        "rising": 2,
        "falling": 3
    }

    def __init__(self):
        self.handle: ctypes.c_int16 = ctypes.c_int16()
        self.frequency: Optional[int] = None
        self.samples: Optional[int] = None
        self.timebase: Optional[int] = None
        self.buffers: MutableMapping = {}
        self.ranges: MutableMapping = {}

    def open(self) -> None:
        assert_pico_ok(self.__dispatch_call("OpenUnit", ctypes.byref(self.handle)))

    @property
    def channels(self):
        return list(self.CHANNELS.keys())

    def get_variant(self):
        info = (ctypes.c_int8 * 6)()
        size = ctypes.c_int16()
        assert_pico_ok(self.__dispatch_call("GetUnitInfo", self.handle, ctypes.byref(info), 6,
                                            ctypes.byref(size), 3))
        return "".join(chr(i) for i in info[:size])

    def setup_frequency(self, frequency: int, samples: int) -> Tuple[int, int]:
        return self.set_frequency(frequency, samples)

    # channel setup (ranges, coupling, which channel is scope vs trigger)
    def set_channel(self, channel: str, enabled: bool, coupling: str, range: float):
        assert_pico_ok(
                self.__dispatch_call("SetChannel", self.handle, self.CHANNELS[channel], enabled,
                                     self.COUPLING[coupling], self.RANGES[range]))
        self.ranges[channel] = range

    def setup_channel(self, channel: str, coupling: str, range: float, enable: bool):
        self.set_channel(channel, enable, coupling, range)

    def _set_freq(self, frequency: int, samples: int, period_bound: float, timebase_bound: int,
                  low_freq: int, high_freq: int, high_subtract: int) -> Tuple[int, int]:
        period = 1 / frequency
        if low_freq == 0 or period > period_bound:
            tb = floor(high_freq / frequency + high_subtract)
            actual_frequency = high_freq // (tb - high_subtract)
        else:
            tb = floor(log2(low_freq) - log2(frequency))
            if tb > timebase_bound:
                tb = timebase_bound
            actual_frequency = low_freq // 2 ** tb
        max_samples = ctypes.c_int32()
        assert_pico_ok(self.__dispatch_call("GetTimebase", self.handle, tb, samples, None, 0,
                                            ctypes.byref(max_samples), 0))
        if max_samples.value < samples:
            samples = max_samples.value
        self.frequency = actual_frequency
        self.samples = samples
        self.timebase = tb
        return actual_frequency, samples

    # frequency setup
    def set_frequency(self, frequency: int, samples: int) -> Tuple[int, int]:
        raise NotImplementedError

    def setup_trigger(self, channel: str, threshold: float, direction: str, delay: int,
                      timeout: int, enable: bool):
        self.set_trigger(direction, enable, threshold, channel, delay, timeout)

    # triggering setup
    def set_trigger(self, type: str, enabled: bool, value: float, channel: str,
                    delay: int, timeout: int):
        assert_pico_ok(
                self.__dispatch_call("SetSimpleTrigger", self.handle, enabled,
                                     self.CHANNELS[channel],
                                     volt2adc(value, self.ranges[channel], self.MAX_ADC_VALUE),
                                     self.TRIGGERS[type], delay, timeout))

    def setup_capture(self, channel: str, enable: bool):
        self.set_buffer(channel, enable)

    # buffer setup
    def set_buffer(self, channel: str, enable: bool):
        if self.samples is None:
            raise ValueError
        if enable:
            if channel in self.buffers:
                del self.buffers[channel]
            buffer = (ctypes.c_int16 * self.samples)()
            assert_pico_ok(self.__dispatch_call("SetDataBuffer", self.handle, self.CHANNELS[channel],
                                                ctypes.byref(buffer), self.samples))
            self.buffers[channel] = buffer
        else:
            assert_pico_ok(self.__dispatch_call("SetDataBuffer", self.handle, self.CHANNELS[channel],
                                                None, self.samples))
            del self.buffers[channel]

    def arm(self):
        if self.samples is None or self.timebase is None:
            raise ValueError
        assert_pico_ok(
                self.__dispatch_call("RunBlock", self.handle, 0, self.samples, self.timebase, 0,
                                     None,
                                     0, None, None))

    def capture(self, channel: str, timeout: Optional[int] = None) -> Optional[np.ndarray]:
        start = time_ns()
        if self.samples is None:
            raise ValueError
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            sleep(0.001)
            assert_pico_ok(self.__dispatch_call("IsReady", self.handle, ctypes.byref(ready)))
            if timeout is not None and (time_ns() - start) / 1e6 >= timeout:
                return None

        actual_samples = ctypes.c_int32(self.samples)
        overflow = ctypes.c_int16()
        assert_pico_ok(
                self.__dispatch_call("GetValues", self.handle, 0, ctypes.byref(actual_samples), 1,
                                     0, 0,
                                     ctypes.byref(overflow)))
        arr = np.array(self.buffers[channel], dtype=np.int16)
        return adc2volt(arr, self.ranges[channel], self.MAX_ADC_VALUE)

    # stop
    def stop(self):
        assert_pico_ok(self.__dispatch_call("Stop"))

    def close(self):
        assert_pico_ok(self.__dispatch_call("CloseUnit", self.handle))

    def __dispatch_call(self, name, *args, **kwargs):
        method = getattr(self.MODULE, self.PREFIX + name)
        if method is None:
            raise ValueError
        return method(*args, **kwargs)


@public
class PS4000Scope(PicoScopeSdk):  # pragma: no cover
    MODULE = ps4000
    PREFIX = "ps4000"
    CHANNELS = {
        "A": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_A"],
        "B": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_B"],
        "C": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_C"],
        "D": ps4000.PS4000_CHANNEL["PS4000_CHANNEL_D"]
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
        100.0: ps4000.PS4000_RANGE["PS4000_100V"]
    }

    MAX_ADC_VALUE = 32764
    MIN_ADC_VALUE = -32764

    COUPLING = {
        "AC": ps4000.PICO_COUPLING["AC"],
        "DC": ps4000.PICO_COUPLING["DC"]
    }

    def set_frequency(self, frequency: int, samples: int):
        variant = self.get_variant()
        if variant in ("4223", "4224", "4423", "4424"):
            return self._set_freq(frequency, samples, 50e-9, 2, 80_000_000, 20_000_000, 1)
        elif variant in ("4226", "4227"):
            return self._set_freq(frequency, samples, 32e-9, 3, 250_000_000, 31_250_000, 2)
        elif variant == "4262":
            return self._set_freq(frequency, samples, 0, 0, 0, 10_000_000, -1)


@public
class PS6000Scope(PicoScopeSdk):  # pragma: no cover
    MODULE = ps6000
    PREFIX = "ps6000"
    CHANNELS = {
        "A": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_A"],
        "B": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_B"],
        "C": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_C"],
        "D": ps6000.PS6000_CHANNEL["PS6000_CHANNEL_D"]
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
        50.0: ps6000.PS6000_RANGE["PS6000_50V"]
    }

    MAX_ADC_VALUE = 32512
    MIN_ADC_VALUE = -32512

    COUPLING = {
        "AC": ps6000.PS6000_COUPLING["PS6000_AC"],
        "DC": ps6000.PS6000_COUPLING["PS6000_DC_1M"]
    }

    def open(self):
        assert_pico_ok(ps6000.ps6000OpenUnit(ctypes.byref(self.handle), None))

    def set_channel(self, channel: str, enabled: bool, coupling: str, range: float):
        assert_pico_ok(ps6000.ps6000SetChannel(self.handle, self.CHANNELS[channel], enabled,
                                               self.COUPLING[coupling], self.RANGES[range], 0,
                                               ps6000.PS6000_BANDWIDTH_LIMITER["PS6000_BW_FULL"]))

    def set_buffer(self, channel: str, enable: bool):
        if self.samples is None:
            raise ValueError
        if enable:
            if channel in self.buffers:
                del self.buffers[channel]
            buffer = (ctypes.c_int16 * self.samples)()
            assert_pico_ok(
                    ps6000.ps6000SetDataBuffer(self.handle, self.CHANNELS[channel],
                                               ctypes.byref(buffer),
                                               self.samples, 0))
            self.buffers[channel] = buffer
        else:
            assert_pico_ok(
                    ps6000.ps6000SetDataBuffer(self.handle, self.CHANNELS[channel],
                                               None,
                                               self.samples, 0))
            del self.buffers[channel]

    def set_frequency(self, frequency: int, samples: int):
        return self._set_freq(frequency, samples, 3.2e-9, 4, 5_000_000_000, 156_250_000, 4)
