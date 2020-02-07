from typing import Optional, Tuple, Sequence

import numpy as np
from chipwhisperer.capture.scopes.base import ScopeTemplate
from public import public

from .base import Scope

@public
class ChipWhispererScope(Scope):
    """A ChipWhisperer based scope."""

    def __init__(self, scope: ScopeTemplate):
        self.scope = scope

    def open(self) -> None:
        self.scope.con()

    @property
    def channels(self) -> Sequence[str]:
        return ["tio1", "tio2", "tio3", "tio4"]

    def setup_frequency(self, frequency: int, samples: int) -> Tuple[int, int]:
        pass

    def setup_channel(self, channel: str, coupling: str, range: float, enable: bool) -> None:
        pass

    def setup_trigger(self, channel: str, threshold: float, direction: str, delay: int,
                      timeout: int, enable: bool) -> None:
        pass

    def setup_capture(self, channel: str, enable: bool) -> None:
        pass

    def arm(self) -> None:
        pass

    def capture(self, channel: str, timeout: Optional[int] = None) -> Optional[np.ndarray]:
        pass

    def stop(self) -> None:
        pass

    def close(self) -> None:
        pass

