"""Provides the Pippenger (bucket) multi-scalar multiplier."""

from copy import copy
from math import ceil
from typing import List, Optional

from public import public

from pyecsca.ec.formula import AdditionFormula, DoublingFormula, ScalingFormula
from pyecsca.ec.mult.base import AccumulationOrder
from pyecsca.ec.mult.msm.base import (
    MultiScalarMultiplier,
    MultiScalarMultiplierAction,
)
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


@public
class PippengerMultiplier(MultiScalarMultiplier):
    """
    Pippenger (bucket method) multi-scalar multiplier.

    Computes the sum of the products of the points with their scalars using `b`-bit windows and
    ``2**b`` buckets per window, see [Pip76]_. The scalar windows are gathered into buckets and
    the buckets are accumulated in a single pass, which makes the per-window cost independent of
    the number of points.

    .. note::
        The bucket accumulation feeds special point pairs to the addition formula: the running
        sum may add a point to itself (when a bucket is empty, the result equals the running sum
        and ``R = R + C`` becomes ``C + C``) and it may cancel a point with its negation
        (``P + (-P)``). The provided addition and doubling formulas therefore must be
        **complete**, i.e. they must handle these cases without a special-case branch.

    :param width: The window width (number of bits per window).
    :param complete: Whether it processes the full order-bit-length of the scalars.
    :param accumulation_order: The order of accumulation of points.
    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    width: int
    """The window width (number of bits per window)."""
    complete: bool
    """Whether it processes the full order-bit-length of the scalars."""
    skip_zero: bool
    """Whether it skips zero-value windows and assigns the first point to the bucket (w/o addition)."""
    accumulation_order: AccumulationOrder
    """The order of accumulation of points."""
    _points: List[Point]

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        width: int,
        scl: Optional[ScalingFormula] = None,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
        complete: bool = True,
        skip_zero: bool = True,
        short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit,
            add=add,
            dbl=dbl,
            scl=scl,
        )
        if width < 1:
            raise ValueError("Invalid window width.")
        self.width = width
        self.accumulation_order = accumulation_order
        self.complete = complete
        self.skip_zero = skip_zero

    def __hash__(self):
        return hash(
            (
                PippengerMultiplier,
                super().__hash__(),
                self.width,
                self.accumulation_order,
                self.complete,
                self.skip_zero
            )
        )

    def __eq__(self, other):
        if not isinstance(other, PippengerMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.width == other.width
            and self.accumulation_order == other.accumulation_order
            and self.complete == other.complete
            and self.skip_zero == other.skip_zero
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, width={self.width}, accumulation_order={self.accumulation_order.name}, complete={self.complete}, skip_zero={self.skip_zero})"

    def _accumulate(self, p: Point, r: Point) -> Point:
        if self.accumulation_order is AccumulationOrder.PeqPR:
            p = self._add(p, r)
        elif self.accumulation_order is AccumulationOrder.PeqRP:
            p = self._add(r, p)
        return p

    def init(
        self, params: DomainParameters, points: List[Point], bits: Optional[int] = None
    ):
        super().init(params, points, bits)
        self._points = list(points)

    def multiply(self, scalars: List[int]) -> Point:
        if not self._initialized:
            raise ValueError("MultiScalarMultiplier not initialized.")
        if len(scalars) != len(self._points):
            raise ValueError("Number of scalars does not match number of points.")
        with MultiScalarMultiplierAction(
            self._points, self._params, scalars
        ) as action:
            neutral = self._params.curve.neutral
            if not scalars or not any(scalars):
                return action.exit(copy(neutral))
            if self.complete:
                max_bits = self._bits
            else:
                max_bits = max(s.bit_length() for s in scalars)
            mask = (1 << self.width) - 1
            num_windows = max(1, ceil(max_bits / self.width))
            result = copy(neutral)
            for i in range(num_windows - 1, -1, -1):
                # Scale the acummulated result (windows computed left-to-right).
                if i != num_windows - 1:
                    for _ in range(self.width):
                        result = self._dbl(result)
                # Initialize buckets to point-at-infinty.
                buckets = [copy(neutral) for _ in range(1 << self.width)]
                # Accumulate points into buckets.
                for j, point in enumerate(self._points):
                    window = (scalars[j] >> (self.width * i)) & mask
                    if self.skip_zero:
                        # Skip zero-value windows.
                        if window:
                            # Assign the first point into the bucket without addition.
                            if buckets[window] == neutral:
                                buckets[window] = point
                            else:
                                buckets[window] = self._accumulate(buckets[window], point)
                    else:
                        buckets[window] = self._accumulate(buckets[window], point)
                # Aggregate the buckets together.
                carry = copy(neutral)
                for b in range((1 << self.width) - 1, 0, -1):
                    carry = self._accumulate(carry, buckets[b])
                    result = self._accumulate(result, carry)
            if "scl" in self.formulas:
                result = self._scl(result)
            return action.exit(result)
