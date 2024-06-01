"""
Provides leakage models to simulate leakage.
"""
import abc
import sys
from typing import Literal, ClassVar

from numpy.random import default_rng
from public import public

from pyecsca.sca.trace import Trace

if sys.version_info[0] < 3 or sys.version_info[0] == 3 and sys.version_info[1] < 10:
    def hw(i):
        return bin(i).count("1")
else:
    def hw(i):
        return i.bit_count()


@public
class Noise:
    pass


@public
class ZeroNoise(Noise):
    def __call__(self, *args, **kwargs):
        return args[0]


@public
class NormalNoice(Noise):
    """
    https://www.youtube.com/watch?v=SAfq55aiqPc
    """

    def __init__(self, mean: float, sdev: float):
        self.rng = default_rng()
        self.mean = mean
        self.sdev = sdev

    def __call__(self, *args, **kwargs):
        arg = args[0]
        if isinstance(arg, Trace):
            return Trace(arg.samples + self.rng.normal(self.mean, self.sdev, len(arg.samples)))
        return arg + self.rng.normal(self.mean, self.sdev)


@public
class LeakageModel(abc.ABC):
    """An abstract leakage model."""
    num_args: ClassVar[int]

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> int:
        """Get the leakage from the arg(s)."""
        raise NotImplementedError


@public
class Identity(LeakageModel):
    """Identity leakage model, leaks the thing itself."""
    num_args = 1

    def __call__(self, *args, **kwargs) -> int:
        return int(args[0])


@public
class Bit(LeakageModel):
    """Bit leakage model, leaks a selected bit."""
    num_args = 1

    def __init__(self, which: int):
        if which < 0:
            raise ValueError("which must be >= 0.")
        self.which = which
        self.mask = 1 << which

    def __call__(self, *args, **kwargs) -> Literal[0, 1]:
        return (int(args[0]) & self.mask) >> self.which  # type: ignore


@public
class Slice(LeakageModel):
    """Slice leakage model, leaks a slice of bits."""
    num_args = 1

    def __init__(self, begin: int, end: int):
        if begin > end:
            raise ValueError("begin must be <= than end.")
        self.begin = begin
        self.end = end
        self.mask = 0
        for i in range(begin, end):
            self.mask |= 1 << i

    def __call__(self, *args, **kwargs) -> int:
        return (int(args[0]) & self.mask) >> self.begin


@public
class HammingWeight(LeakageModel):
    """Hamming-weight leakage model, leaks the Hamming-weight of the thing."""
    num_args = 1

    def __call__(self, *args, **kwargs) -> int:
        return hw(int(args[0]))


@public
class HammingDistance(LeakageModel):
    """Hamming-distance leakage model, leaks the Hamming-distance between the two things."""
    num_args = 2

    def __call__(self, *args, **kwargs) -> int:
        return hw(int(args[0]) ^ int(args[1]))


@public
class BitLength(LeakageModel):
    """Bit-length leakage model, leaks the bit-length of the thing."""
    num_args = 1

    def __call__(self, *args, **kwargs) -> int:
        return int(args[0]).bit_length()
