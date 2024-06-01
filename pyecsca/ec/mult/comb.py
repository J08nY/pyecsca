"""Provides Comb-like scalar multipliers, such as BGMW or Lim-Lee."""
from copy import copy
from math import ceil
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
from pyecsca.ec.scalar import convert_base


@public
class BGMWMultiplier(AccumulatorMultiplier, ScalarMultiplier):
    """
    Brickell, Gordon, McCurley and Wilson (BGMW) scalar multiplier,
    or rather, its one parametrization.

    Algorithm 3.41 from [GECC]_

    :param width: Window width.
    :param direction: Whether it is LTR or RTL.
    :param accumulation_order: The order of accumulation of points.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    direction: ProcessingDirection
    """Whether it is LTR or RTL."""
    width: int
    """Window width."""
    _points: MutableMapping[int, Point]

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        width: int,
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
            scl=scl,
        )
        self.direction = direction
        self.width = width

    def __hash__(self):
        return hash(
            (
                BGMWMultiplier,
                super().__hash__(),
                self.width,
                self.direction,
                self.accumulation_order,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, BGMWMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.width == other.width
            and self.direction == other.direction
            and self.accumulation_order == other.accumulation_order
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, width={self.width}, direction={self.direction.name}, accumulation_order={self.accumulation_order.name})"

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            d = ceil(params.order.bit_length() / self.width)
            self._points = {}
            current_point = point
            for i in range(d):
                self._points[i] = current_point
                if i != d - 1:
                    for _ in range(self.width):
                        current_point = self._dbl(current_point)

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            a = copy(self._params.curve.neutral)
            b = copy(self._params.curve.neutral)
            recoded = convert_base(scalar, 2**self.width)
            for j in range(2**self.width - 1, 0, -1):
                if self.direction == ProcessingDirection.RTL:
                    for i, ki in enumerate(recoded):
                        if ki == j:
                            b = self._accumulate(b, self._points[i])
                elif self.direction == ProcessingDirection.LTR:
                    for i, ki in reversed(list(enumerate(recoded))):
                        if ki == j:
                            b = self._accumulate(b, self._points[i])
                if self.short_circuit and a == b:
                    # TODO: Double necessary here for incomplete formulas, maybe another param and not reuse short_cirtuit?
                    a = self._dbl(b)
                else:
                    a = self._accumulate(a, b)
            if "scl" in self.formulas:
                a = self._scl(a)
            return action.exit(a)


@public
class CombMultiplier(AccumulatorMultiplier, ScalarMultiplier):
    """
    Comb multiplier.

    Algorithm 3.44 from [GECC]_

    :param width: Window width (number of comb teeth).
    :param accumulation_order: The order of accumulation of points.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    width: int
    """Window width."""
    _points: MutableMapping[int, Point]

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        width: int,
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
        self.width = width

    def __hash__(self):
        return hash(
            (CombMultiplier, super().__hash__(), self.width, self.accumulation_order)
        )

    def __eq__(self, other):
        if not isinstance(other, CombMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
            and self.width == other.width
            and self.accumulation_order == other.accumulation_order
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, width={self.width}, accumulation_order={self.accumulation_order.name})"

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            d = ceil(params.order.bit_length() / self.width)
            base_points = {}
            current_point = point
            for i in range(self.width):
                base_points[i] = current_point
                if i != d - 1:
                    for _ in range(d):
                        current_point = self._dbl(current_point)
            self._points = {}
            for j in range(1, 2**self.width):
                points = []
                for i in range(self.width):
                    if j & (1 << i):
                        points.append(base_points[i])
                self._points[j] = points[0]
                for other in points[1:]:
                    self._points[j] = self._accumulate(self._points[j], other)

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            q = copy(self._params.curve.neutral)
            d = ceil(self._params.order.bit_length() / self.width)
            recoded = convert_base(scalar, 2**d)
            if len(recoded) != self.width:
                recoded.extend([0] * (self.width - len(recoded)))
            for i in range(d - 1, -1, -1):
                q = self._dbl(q)
                word = 0
                for j in range(self.width):
                    # get i-th bit of recoded[j] and set it into the j-th bit of word
                    bit = (recoded[j] >> i) & 1
                    word |= bit << j
                if word:
                    q = self._accumulate(q, self._points[word])
                # TODO always

            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)
