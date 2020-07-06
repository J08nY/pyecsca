from typing import Optional, Tuple, Sequence, Set

import numpy as np
from chipwhisperer.capture.scopes.OpenADC import OpenADC
from public import public

from .base import Scope, SampleType
from ..trace import Trace


@public
class ChipWhispererScope(Scope):  # pragma: no cover
    """A ChipWhisperer based scope."""

    def __init__(self, scope: OpenADC):
        super().__init__()
        self.scope = scope
        self.triggers: Set[str] = set()

    def open(self) -> None:
        self.scope.con()

    @property
    def channels(self) -> Sequence[str]:
        return []

    def setup_frequency(self, frequency: int, pretrig: int, posttrig: int) -> Tuple[int, int]:
        if pretrig != 0:
            raise ValueError("ChipWhisperer does not support pretrig samples.")
        self.scope.clock.clkgen_freq = frequency
        self.scope.samples = posttrig
        return self.scope.clock.freq_ctr, self.scope.samples

    def setup_channel(self, channel: str, coupling: str, range: float, offset: float, enable: bool) -> None:
        pass

    def setup_trigger(self, channel: str, threshold: float, direction: str, delay: int,
                      timeout: int, enable: bool) -> None:
        if enable:
            self.triggers.add(channel)
        elif channel in self.triggers:
            self.triggers.remove(channel)
        self.scope.adc.basic_mode = direction
        self.scope.trigger.triggers = " OR ".join(self.triggers)

    def setup_capture(self, channel: str, enable: bool) -> None:
        pass

    def arm(self) -> None:
        self.scope.arm()

    def capture(self, timeout: Optional[int] = None) -> bool:
        return not self.scope.capture()

    def retrieve(self, channel: str, type: SampleType, dtype=np.float16) -> Optional[Trace]:
        data = self.scope.get_last_trace()
        if data is None:
            return None
        return Trace(np.array(data, dtype=dtype), {"sampling_frequency": self.scope.clock.clkgen_freq, "channel": channel})

    def stop(self) -> None:
        pass

    def close(self) -> None:
        self.scope.dis()
