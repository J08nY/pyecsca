"""Provides sliding window and fixed window scalar multipliers (including m-ary, for non power-of-2 m)."""

from copy import copy
from typing import Optional, MutableMapping
from public import public

from pyecsca.ec.params import DomainParameters
from pyecsca.ec.mult.base import (
    ScalarMultiplier,
    AccumulationOrder,
    ScalarMultiplicationAction,
    PrecomputationAction,
    ProcessingDirection,
    AccumulatorMultiplier,
    PrecompMultiplier,
)
from pyecsca.ec.formula import (
    AdditionFormula,
    DoublingFormula,
    ScalingFormula,
    NegationFormula,
)
from pyecsca.ec.point import Point
from pyecsca.ec.scalar import (
    convert_base,
    sliding_window_rtl,
    sliding_window_ltr,
    booth_window,
)


@public
class SlidingWindowMultiplier(
    AccumulatorMultiplier, PrecompMultiplier, ScalarMultiplier
):
    """
    Sliding window scalar multiplier.

    :param width: The width of the sliding-window recoding.
    :param recoding_direction: The direction for the sliding-window recoding.
    :param accumulation_order: The order of accumulation of points.
    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    width: int
    """The width of the sliding-window recoding."""
    recoding_direction: ProcessingDirection
    """The direction for the sliding-window recoding."""
    _points: MutableMapping[int, Point]

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        width: int,
        scl: Optional[ScalingFormula] = None,
        recoding_direction: ProcessingDirection = ProcessingDirection.LTR,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
        short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit,
            accumulation_order=accumulation_order,
            add=add,
            dbl=dbl,
            scl=scl,
        )
        self.width = width
        self.recoding_direction = recoding_direction

    def __hash__(self):
        return hash(
            (
                SlidingWindowMultiplier,
                super().__hash__(),
                self.width,
                self.recoding_direction,
                self.accumulation_order,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, SlidingWindowMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.width == other.width
            and self.recoding_direction == other.recoding_direction
            and self.accumulation_order == other.accumulation_order
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, width={self.width}, recoding_direction={self.recoding_direction.name}, accumulation_order={self.accumulation_order.name})"

    def init(self, params: DomainParameters, point: Point, bits: Optional[int] = None):
        with PrecomputationAction(params, point) as action:
            super().init(params, point, bits)
            self._points = {}
            current_point = point
            double_point = self._dbl(point)
            for i in range(0, 2 ** (self.width - 1)):
                self._points[2 * i + 1] = current_point
                current_point = self._add(current_point, double_point)
            action.exit(self._points)

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, self._params, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            if self.recoding_direction is ProcessingDirection.LTR:
                scalar_sliding = sliding_window_ltr(scalar, self.width)
            elif self.recoding_direction is ProcessingDirection.RTL:
                scalar_sliding = sliding_window_rtl(scalar, self.width)
            q = copy(self._params.curve.neutral)
            for val in scalar_sliding:
                q = self._dbl(q)
                if val != 0:
                    q = self._accumulate(q, self._points[val])
            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)


@public
class FixedWindowLTRMultiplier(
    AccumulatorMultiplier, PrecompMultiplier, ScalarMultiplier
):
    """
    Like LTRMultiplier, but m-ary, not binary.

    For `m` a power-of-2 this is a fixed window multiplier
    that works on `log_2(m)` wide windows and uses only doublings
    to perform the multiplication-by-m between each window addition.

    For other `m` values, this is the m-ary multiplier.

    :param m: The arity of the multiplier.
    :param accumulation_order: The order of accumulation of points.
    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                      of the point at infinity.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    m: int
    """The arity of the multiplier."""
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
            short_circuit=short_circuit,
            accumulation_order=accumulation_order,
            add=add,
            dbl=dbl,
            scl=scl,
        )
        if m < 2:
            raise ValueError("Invalid base.")
        self.accumulation_order = accumulation_order
        self.m = m

    def __hash__(self):
        return hash(
            (
                FixedWindowLTRMultiplier,
                super().__hash__(),
                self.m,
                self.accumulation_order,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, FixedWindowLTRMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.m == other.m
            and self.accumulation_order == other.accumulation_order
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, m={self.m}, accumulation_order={self.accumulation_order.name})"

    def init(self, params: DomainParameters, point: Point, bits: Optional[int] = None):
        with PrecomputationAction(params, point) as action:
            super().init(params, point, bits)
            double_point = self._dbl(point)
            self._points = {1: point, 2: double_point}
            current_point = double_point
            for i in range(3, self.m):
                current_point = self._add(current_point, point)
                self._points[i] = current_point
            action.exit(self._points)

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

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, self._params, scalar) as action:
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


@public
class WindowBoothMultiplier(AccumulatorMultiplier, PrecompMultiplier, ScalarMultiplier):
    """

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param width: The width of the window.
    :param accumulation_order: The order of accumulation of points.
    :param precompute_negation: Whether to precompute the negation of the precomputed points as well.
                                It is computed on the fly otherwise.
    """

    requires = {AdditionFormula, DoublingFormula, NegationFormula}
    optionals = {ScalingFormula}
    _points: MutableMapping[int, Point]
    _points_neg: MutableMapping[int, Point]
    precompute_negation: bool = False
    """Whether to precompute the negation of the precomputed points as well."""
    width: int
    """The width of the window."""

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        neg: NegationFormula,
        width: int,
        scl: Optional[ScalingFormula] = None,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
        precompute_negation: bool = False,
        short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit,
            accumulation_order=accumulation_order,
            add=add,
            dbl=dbl,
            neg=neg,
            scl=scl,
        )
        self.width = width
        self.precompute_negation = precompute_negation

    def __hash__(self):
        return hash(
            (
                WindowBoothMultiplier,
                super().__hash__(),
                self.width,
                self.precompute_negation,
                self.accumulation_order,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, WindowBoothMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.width == other.width
            and self.precompute_negation == other.precompute_negation
            and self.accumulation_order == other.accumulation_order
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, width={self.width}, precompute_negation={self.precompute_negation}, accumulation_order={self.accumulation_order.name})"

    def init(self, params: DomainParameters, point: Point, bits: Optional[int] = None):
        with PrecomputationAction(params, point) as actions:
            super().init(params, point, bits)
            double_point = self._dbl(point)
            self._points = {1: point, 2: double_point}
            if self.precompute_negation:
                self._points_neg = {1: self._neg(point), 2: self._neg(double_point)}
            current_point = double_point
            for i in range(3, 2 ** (self.width - 1) + 1):
                current_point = self._add(current_point, point)
                self._points[i] = current_point
                if self.precompute_negation:
                    self._points_neg[i] = self._neg(current_point)
            if self.precompute_negation:
                actions.exit({**self._points, **self._points_neg})
            else:
                actions.exit(self._points)

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, self._params, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            scalar_booth = booth_window(scalar, self.width, self._bits)
            q = copy(self._params.curve.neutral)
            for val in scalar_booth:
                for _ in range(self.width):
                    q = self._dbl(q)
                if val > 0:
                    q = self._accumulate(q, self._points[val])
                elif val < 0:
                    if self.precompute_negation:
                        neg = self._points_neg[-val]
                    else:
                        neg = self._neg(self._points[-val])
                    q = self._accumulate(q, neg)
            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)
