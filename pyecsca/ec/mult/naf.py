"""Provides scalar multipliers based on the Non Adjacent Form (NAF) recoding."""
from copy import copy
from typing import Optional, List, MutableMapping
from public import public

from pyecsca.ec.mult.base import (
    ScalarMultiplier,
    ScalarMultiplicationAction,
    ProcessingDirection,
    AccumulationOrder,
    PrecomputationAction,
    AccumulatorMultiplier,
)
from pyecsca.ec.formula import (
    AdditionFormula,
    DoublingFormula,
    ScalingFormula,
    NegationFormula,
)
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point
from pyecsca.ec.scalar import naf, wnaf


@public
class BinaryNAFMultiplier(AccumulatorMultiplier, ScalarMultiplier):
    """
    Binary NAF (Non Adjacent Form) multiplier.

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param direction: Whether it is LTR or RTL.
    :param accumulation_order: The order of accumulation of points.
    """

    requires = {AdditionFormula, DoublingFormula, NegationFormula}
    optionals = {ScalingFormula}
    direction: ProcessingDirection
    _point_neg: Point

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        neg: NegationFormula,
        scl: Optional[ScalingFormula] = None,
        direction: ProcessingDirection = ProcessingDirection.LTR,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
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
        self.direction = direction

    def __hash__(self):
        return hash(
            (
                BinaryNAFMultiplier,
                super().__hash__(),
                self.direction,
                self.accumulation_order,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, BinaryNAFMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.direction == other.direction
            and self.accumulation_order == other.accumulation_order
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, direction={self.direction.name}, accumulation_order={self.accumulation_order.name})"

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            self._point_neg = self._neg(point)

    def _ltr(self, scalar_naf: List[int]) -> Point:
        q = copy(self._params.curve.neutral)
        for val in scalar_naf:
            q = self._dbl(q)
            if val == 1:
                q = self._accumulate(q, self._point)
            if val == -1:
                # TODO: Whether this negation is precomputed can be a parameter
                q = self._accumulate(q, self._point_neg)
        return q

    def _rtl(self, scalar_naf: List[int]) -> Point:
        q = self._point
        r = copy(self._params.curve.neutral)
        for val in reversed(scalar_naf):
            if val == 1:
                r = self._accumulate(r, q)
            if val == -1:
                neg = self._neg(q)
                r = self._accumulate(r, neg)
            q = self._dbl(q)
        return r

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            scalar_naf = naf(scalar)
            if self.direction is ProcessingDirection.LTR:
                q = self._ltr(scalar_naf)
            elif self.direction is ProcessingDirection.RTL:
                q = self._rtl(scalar_naf)
            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)


@public
class WindowNAFMultiplier(AccumulatorMultiplier, ScalarMultiplier):
    """
    Window NAF (Non Adjacent Form) multiplier, left-to-right.

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
                WindowNAFMultiplier,
                super().__hash__(),
                self.width,
                self.precompute_negation,
                self.accumulation_order,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, WindowNAFMultiplier):
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

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            self._points = {}
            self._points_neg = {}
            current_point = point
            double_point = self._dbl(point)
            for i in range(0, 2 ** (self.width - 2)):
                self._points[2 * i + 1] = current_point
                if self.precompute_negation:
                    self._points_neg[2 * i + 1] = self._neg(current_point)
                current_point = self._add(current_point, double_point)

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            scalar_naf = wnaf(scalar, self.width)
            q = copy(self._params.curve.neutral)
            for val in scalar_naf:
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
