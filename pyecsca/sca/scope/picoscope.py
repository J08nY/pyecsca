import ctypes
from enum import IntEnum
from math import log2, floor
from typing import Mapping, Optional, MutableMapping, Union

import numpy as np
from picosdk.functions import assert_pico_ok
from picosdk.library import Library
from picosdk.ps4000 import ps4000
from picosdk.ps6000 import ps6000
from public import public

from .base import Scope


class TriggerType(IntEnum):
    ABOVE = 1
    BELOW = 2
    RISING = 3
    FALLING = 4


def adc2volt(adc: Union[np.ndarray, ctypes.c_int16], volt_range: float, adc_minmax: int) -> Union[
    np.ndarray, float]:
    if isinstance(adc, ctypes.c_int16):
        adc = adc.value
    return (adc / adc_minmax) * volt_range


def volt2adc(volt: Union[np.ndarray, float], volt_range: float, adc_minmax: int) -> Union[
    np.ndarray, ctypes.c_int16]:
    if isinstance(volt, float):
        return ctypes.c_int16(int((volt / volt_range) * adc_minmax))
    return (volt / volt_range) * adc_minmax


class PicoScope(Scope):
    """A PicoScope based scope."""
    MODULE: Library
    PREFIX: str
    CHANNELS: Mapping
    RANGES: Mapping
    MAX_ADC_VALUE: int
    MIN_ADC_VALUE: int
    COUPLING: Mapping
    TIME_UNITS: Mapping

    def __init__(self):
        self.handle: ctypes.c_int16 = ctypes.c_int16()
        self.frequency: Optional[int] = None
        self.samples: Optional[int] = None
        self.timebase: Optional[int] = None
        self.buffers: MutableMapping = {}
        self.ranges: MutableMapping = {}

    def open(self):
        assert_pico_ok(self.__dispatch_call("OpenUnit", ctypes.byref(self.handle)))

    # channel setup (ranges, coupling, which channel is scope vs trigger)
    def set_channel(self, channel: str, enabled: bool, coupling: str, range: float):
        assert_pico_ok(
                self.__dispatch_call("SetChannel", self.handle, self.CHANNELS[channel], enabled,
                                     self.COUPLING[coupling], self.RANGES[range]))
        self.ranges[channel] = range

    # frequency setup
    def set_frequency(self, frequency: int, samples: int):
        period = 1 / frequency
        if period <= 3.2e-9:
            tb = log2(5_000_000_000) - log2(frequency)
            tb = floor(tb)
            if tb > 4:
                tb = 4
            actual_frequency = 5_000_000_000 / 2 ** tb
        else:
            tb = floor(156_250_000 / frequency + 4)
            actual_frequency = 156_250_000 / (tb - 4)
        max_samples = ctypes.c_int32()
        assert_pico_ok(self.__dispatch_call("GetTimebase", self.handle, tb, samples, None, 0,
                                            ctypes.byref(max_samples), 0))
        if max_samples.value < samples:
            samples = max_samples
        self.frequency = actual_frequency
        self.samples = samples
        self.timebase = tb
        return actual_frequency, samples

    # triggering setup
    def set_trigger(self, type: TriggerType, enabled: bool, value: float, channel: str,
                    range: float, delay: int, timeout: int):
        assert_pico_ok(
                self.__dispatch_call("SetSimpleTrigger", self.handle, enabled,
                                     self.CHANNELS[channel],
                                     volt2adc(value, range, self.MAX_ADC_VALUE),
                                     type.value, delay, timeout))

    # buffer setup
    def set_buffer(self, channel: str):
        if self.samples is None:
            raise ValueError
        buffer = (ctypes.c_int16 * self.samples)()
        self.buffers[channel] = buffer
        assert_pico_ok(self.__dispatch_call("SetDataBuffer", self.handle, self.CHANNELS[channel],
                                            ctypes.byref(buffer), self.samples))

    # collection
    def collect(self):
        if self.samples is None or self.timebase is None:
            raise ValueError
        assert_pico_ok(
                self.__dispatch_call("RunBlock", self.handle, 0, self.samples, self.timebase, 0,
                                     None,
                                     0, None, None))
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            assert_pico_ok(self.__dispatch_call("IsReady", self.handle, ctypes.byref(ready)))

    # get the data
    def retrieve(self, channel: str):
        if self.samples is None:
            raise ValueError
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
class PS4000Scope(PicoScope):
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


@public
class PS6000Scope(PicoScope):
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

    def set_channel(self, channel: str, enabled: bool, coupling: str, range: str):
        assert_pico_ok(ps6000.ps6000SetChannel(self.handle, self.CHANNELS[channel], enabled,
                                               self.COUPLING[coupling], self.RANGES[range], 0,
                                               ps6000.PS6000_BANDWIDTH_LIMITER["PS6000_BW_FULL"]))

    def set_buffer(self, channel: str):
        if self.samples is None:
            raise ValueError
        buffer = (ctypes.c_int16 * self.samples)()
        self.buffers[channel] = buffer
        assert_pico_ok(
                ps6000.ps6000SetDataBuffer(self.handle, self.CHANNELS[channel],
                                           ctypes.byref(buffer),
                                           self.samples, 0))
