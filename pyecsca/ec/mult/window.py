from copy import copy
from typing import Optional, MutableMapping
from public import public

from ..params import DomainParameters
from .base import ScalarMultiplier, AccumulationOrder, ScalarMultiplicationAction, PrecomputationAction
from ..formula import (
    AdditionFormula,
    DoublingFormula,
    ScalingFormula,
)
from ..point import Point
from ..scalar import convert_base


@public
class FixedWindowLTRMultiplier(ScalarMultiplier):
    """Like LTRMultiplier, but not binary, but m-ary."""

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    complete: bool
    m: int
    accumulation_order: AccumulationOrder
    _points: MutableMapping[int, Point]

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            m: int,
            scl: Optional[ScalingFormula] = None,
            accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
            short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit, add=add, dbl=dbl, scl=scl
        )
        if m < 2:
            raise ValueError("Invalid base.")
        self.accumulation_order = accumulation_order
        self.m = m

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, FixedWindowLTRMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.m == other.m

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            double_point = self._dbl(point)
            self._points = {1: point, 2: double_point}
            current_point = double_point
            for i in range(3, self.m):
                current_point = self._add(current_point, point)
                self._points[i] = current_point

    def _mult_m(self, point: Point) -> Point:
        if self.m & (self.m - 1) == 0:
            # Power of 2
            q = point
            for _ in range(self.m.bit_length() - 1):
                q = self._dbl(q)
        else:
            # Not power of 2
            r = copy(point)
            q = self._dbl(point)
            # TODO: This could be made via a different chain.
            for _ in range(self.m - 2):
                q = self._accumulate(q, r)
        return q

    def _accumulate(self, p: Point, r: Point) -> Point:
        if self.accumulation_order is AccumulationOrder.PeqPR:
            p = self._add(p, r)
        elif self.accumulation_order is AccumulationOrder.PeqRP:
            p = self._add(r, p)
        return p

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            # General case (any m) and special case (m = 2^k) are handled together here
            converted = convert_base(scalar, self.m)
            q = copy(self._params.curve.neutral)
            for digit in reversed(converted):
                q = self._mult_m(q)
                if digit != 0:
                    q = self._accumulate(q, self._points[digit])
            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)
