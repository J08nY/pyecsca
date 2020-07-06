from time import time_ns, sleep
import numpy as np
from typing import Optional, Tuple, Sequence, Union

from picoscope.ps3000 import PS3000
from picoscope.ps4000 import PS4000
from picoscope.ps5000 import PS5000
from picoscope.ps6000 import PS6000
from public import public

from .base import Scope, SampleType
from ..trace import Trace


@public
class PicoScopeAlt(Scope):  # pragma: no cover

    def __init__(self, ps: Union[PS3000, PS4000, PS5000, PS6000]):
        super().__init__()
        self.ps = ps
        self.trig_ratio: float = 0.0
        self.frequency: Optional[float] = None

    def open(self) -> None:
        self.ps.open()

    @property
    def channels(self) -> Sequence[str]:
        return list(self.ps.CHANNELS.keys())

    def setup_frequency(self, frequency: int, pretrig: int, posttrig: int) -> Tuple[int, int]:
        samples = pretrig + posttrig
        actual_frequency, max_samples = self.ps.setSamplingFrequency(frequency, samples)
        if max_samples < samples:
            self.trig_ratio = (pretrig / samples)
            samples = max_samples
        self.frequency = actual_frequency
        return actual_frequency, samples

    def setup_channel(self, channel: str, coupling: str, range: float, offset: float, enable: bool) -> None:
        self.ps.setChannel(channel, coupling, range, offset, enable)

    def setup_trigger(self, channel: str, threshold: float, direction: str, delay: int,
                      timeout: int, enable: bool) -> None:
        self.ps.setSimpleTrigger(channel, threshold, direction, delay, timeout, enable)

    def setup_capture(self, channel: str, enable: bool) -> None:
        pass

    def arm(self) -> None:
        self.ps.runBlock()

    def capture(self, timeout: Optional[int] = None) -> bool:
        start = time_ns()
        while not self.ps.isReady():
            sleep(0.001)
            if timeout is not None and (time_ns() - start) / 1e6 >= timeout:
                return False
        return True

    def retrieve(self, channel: str, type: SampleType, dtype=np.float32) -> Optional[Trace]:
        if type == SampleType.Raw:
            data = self.ps.getDataRaw(channel).astype(dtype=dtype, copy=False)
        else:
            data = self.ps.getDataV(channel, dtype=dtype)
        if data is None:
            return None
        return Trace(data, {"sampling_frequency": self.frequency, "channel": channel, "sample_type": type})

    def stop(self) -> None:
        self.ps.stop()

    def close(self) -> None:
        self.ps.close()
