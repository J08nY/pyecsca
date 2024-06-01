"""Provides fixed-base scalar multipliers that do a lot of pre-computation (but not combs)."""
from copy import copy
from typing import MutableMapping, Optional

from public import public

from pyecsca.ec.formula import AdditionFormula, DoublingFormula, ScalingFormula
from pyecsca.ec.mult import (
    AccumulatorMultiplier,
    ScalarMultiplier,
    ProcessingDirection,
    AccumulationOrder,
    PrecomputationAction,
    ScalarMultiplicationAction,
)
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


@public
class FullPrecompMultiplier(AccumulatorMultiplier, ScalarMultiplier):
    """
    See page 104 of [GECC]_:

        For example, if the points `[2]P,[2^2]P,...,[2^t−1]P` are precomputed, then the right-to-left
        binary method (Algorithm 3.26) has expected running time `(m/2)A` (all doublings are
        eliminated).

    :param always: Whether the addition is always performed.
    :param direction: Whether it is LTR or RTL.
    :param accumulation_order: The order of accumulation of points.
    :param complete: Whether it starts processing at full order-bit-length.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    always: bool
    """Whether the double and add always method is used."""
    direction: ProcessingDirection
    """Whether it is LTR or RTL."""
    complete: bool
    """Whether it starts processing at full order-bit-length."""
    _points: MutableMapping[int, Point]

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        scl: Optional[ScalingFormula] = None,
        always: bool = False,
        direction: ProcessingDirection = ProcessingDirection.LTR,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
        complete: bool = True,
        short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit,
            accumulation_order=accumulation_order,
            add=add,
            dbl=dbl,
            scl=scl,
        )
        self.always = always
        self.direction = direction
        self.complete = complete

    def __hash__(self):
        return hash(
            (
                FullPrecompMultiplier,
                super().__hash__(),
                self.direction,
                self.accumulation_order,
                self.always,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, FullPrecompMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.direction == other.direction
            and self.accumulation_order == other.accumulation_order
            and self.always == other.always
            and self.complete == other.complete
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, accumulation_order={self.accumulation_order.name}, always={self.always}, complete={self.complete})"

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            self._points = {}
            current_point = point
            for i in range(params.order.bit_length() + 1):
                self._points[i] = current_point
                if i != params.order.bit_length():
                    current_point = self._dbl(current_point)

    def _ltr(self, scalar: int) -> Point:
        if self.complete:
            top = self._params.order.bit_length() - 1
        else:
            top = scalar.bit_length() - 1
        r = copy(self._params.curve.neutral)
        for i in range(top, -1, -1):
            if scalar & (1 << i) != 0:
                r = self._accumulate(r, self._points[i])
            elif self.always:
                # dummy add
                self._accumulate(r, self._points[i])
        return r

    def _rtl(self, scalar: int) -> Point:
        r = copy(self._params.curve.neutral)
        if self.complete:
            top = self._params.order.bit_length()
        else:
            top = scalar.bit_length()
        for i in range(top):
            if scalar & 1 != 0:
                r = self._accumulate(r, self._points[i])
            elif self.always:
                # dummy add
                self._accumulate(r, self._points[i])
            scalar >>= 1
        return r

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            if self.direction is ProcessingDirection.LTR:
                r = self._ltr(scalar)
            elif self.direction is ProcessingDirection.RTL:
                r = self._rtl(scalar)
            if "scl" in self.formulas:
                r = self._scl(r)
            return action.exit(r)
