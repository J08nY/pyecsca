from enum import Enum, auto
from typing import Tuple, Sequence, Optional

from public import public

from ..trace import Trace


@public
class SampleType(Enum):
    Raw = auto()
    Volt = auto()


@public
class Scope(object):
    """An oscilloscope."""

    def open(self) -> None:
        """Open the connection to the scope."""
        raise NotImplementedError

    @property
    def channels(self) -> Sequence[str]:
        """A list of channels available on this scope."""
        raise NotImplementedError

    def setup_frequency(self, frequency: int, pretrig: int, posttrig: int) -> Tuple[int, int]:
        """
        Setup the frequency and sample count for the measurement. The scope might not support
        the requested values and will adjust them to get the next best frequency and the largest
        supported number of samples (or the number of samples requested).

        :param frequency: The requested frequency in Hz.
        :param pretrig: The requested number of samples to measure before the trigger.
        :param posttrig: The requested number of samples to measure after the trigger.
        :return: A tuple of the actual set frequency and the actual number of samples.
        """
        raise NotImplementedError

    def setup_channel(self, channel: str, coupling: str, range: float, offset: float,
                      enable: bool) -> None:
        """
        Setup a channel to use the coupling method and measure the given voltage range.

        :param channel: The channel to measure.
        :param coupling: The coupling method ("AC" or "DC).
        :param range: The voltage range to measure.
        :param offset: The analog voltage offset added to the input. Not supported on many scopes.
        :param enable: Whether to enable or disable the channel.
        """
        raise NotImplementedError

    def setup_trigger(self, channel: str, threshold: float, direction: str, delay: int,
                      timeout: int, enable: bool) -> None:
        """
        Setup a trigger on a particular `channel`, the channel has to be set up and enabled.
        The trigger will fire based on the `threshold` and `direction`, if enabled,  the trigger
        will capture after `delay` ticks pass. If trigger conditions do not hold it will fire
        automatically after `timeout` milliseconds.

        :param channel: The channel to trigger on.
        :param threshold: The value to trigger on.
        :param direction: The direction to trigger on ("above", "below", "rising", "falling").
        :param delay: The delay for capture after trigger (clock ticks).
        :param timeout: The timeout in milliseconds.
        :param enable: Whether to enable or disable this trigger.
        """
        raise NotImplementedError

    def setup_capture(self, channel: str, enable: bool) -> None:
        """
        Setup the capture for a channel.

        :param channel: The channel to capture.
        :param enable: Whether to enable or disable capture.
        """
        raise NotImplementedError

    def arm(self) -> None:
        """Arm the scope, it will listen for the trigger after this point."""
        raise NotImplementedError

    def capture(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for the trace to capture, this will block until the scope has a trace.

        :param timeout: A time in milliseconds to wait for the trace, returns `None` if it runs out.
        :return: Whether capture was successful (or it timed out).
        """
        raise NotImplementedError

    def retrieve(self, channel: str, type: SampleType, dtype=None) -> Optional[Trace]:
        """
        Retrieve a captured trace of a channel.

        :param channel: The channel to retrieve the trace from.
        :param type: The type of returned samples.
        :param dtype: The data type of the returned samples, should be numpy dtype-like.
        :return: The captured trace (if any).
        """
        raise NotImplementedError

    def stop(self) -> None:
        """Stop the capture, if any."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the connection to the scope."""
        raise NotImplementedError
