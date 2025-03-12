"""Provides several countermeasures against side-channel attacks."""

from abc import ABC, abstractmethod
from typing import Optional

from public import public

from pyecsca.ec.formula import AdditionFormula
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


@public
class ScalarMultiplierCountermeasure(ABC):
    """
    A scalar multiplier-based countermeasure.

    This class behaves like a scalar multiplier, in fact it wraps one
    and provides some scalar-splitting countermeasure.
    """

    mult: ScalarMultiplier
    params: Optional[DomainParameters]
    point: Optional[Point]

    def __init__(self, mult: ScalarMultiplier):
        self.mult = mult

    def init(self, params: DomainParameters, point: Point):
        self.params = params
        self.point = point
        self.mult.init(self.params, self.point)

    @abstractmethod
    def multiply(self, scalar: int) -> Point:
        raise NotImplementedError


@public
class GroupScalarRandomization(ScalarMultiplierCountermeasure):
    rand_bits: int

    def __init__(self, mult: ScalarMultiplier, rand_bits: int = 32):
        super().__init__(mult)
        self.rand_bits = rand_bits

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")
        order = self.params.order
        mask = int(Mod.random(1 << self.rand_bits))
        masked_scalar = scalar + mask * order
        return self.mult.multiply(masked_scalar)


@public
class AdditiveSplitting(ScalarMultiplierCountermeasure):
    add: Optional[AdditionFormula]

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None):
        super().__init__(mult)
        self.add = add

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")

        order = self.params.order
        r = Mod.random(order)
        s = scalar - r
        R = self.mult.multiply(int(r))
        S = self.mult.multiply(int(s))
        if self.add is None:
            return self.mult._add(R, S)  # noqa: This is OK.
        else:
            return self.add(
                self.params.curve.prime, R, S, **self.params.curve.parameters
            )[0]


@public
class MultiplicativeSplitting(ScalarMultiplierCountermeasure):
    rand_bits: int

    def __init__(self, mult: ScalarMultiplier, rand_bits: int = 32):
        super().__init__(mult)
        self.rand_bits = rand_bits

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")
        r = Mod.random(1 << self.rand_bits)
        R = self.mult.multiply(int(r))

        self.mult.init(self.params, R)
        kr_inv = scalar * mod(int(r), self.params.order).inverse()
        return self.mult.multiply(int(kr_inv))


@public
class EuclideanSplitting(ScalarMultiplierCountermeasure):
    add: Optional[AdditionFormula]

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None):
        super().__init__(mult)
        self.add = add

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")

        order = self.params.order
        half_bits = order.bit_length() // 2
        r = Mod.random(1 << half_bits)
        R = self.mult.multiply(int(r))

        k1 = scalar % int(r)
        k2 = scalar // int(r)
        T = self.mult.multiply(k1)

        self.mult.init(self.params, R)
        S = self.mult.multiply(k2)
        if self.add is None:
            return self.mult._add(S, T)  # noqa: This is OK.
        else:
            return self.add(
                self.params.curve.prime, S, T, **self.params.curve.parameters
            )[0]
