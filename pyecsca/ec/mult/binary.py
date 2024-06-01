"""Provides binary scalar multipliers (LTR and RTL), that process the scalar as-is, bit-by-bit."""
from abc import ABC
from copy import copy
from typing import Optional

from public import public

from pyecsca.ec.mult.base import (
    ScalarMultiplier,
    ProcessingDirection,
    AccumulationOrder,
    ScalarMultiplicationAction,
    AccumulatorMultiplier,
)
from pyecsca.ec.formula import AdditionFormula, DoublingFormula, ScalingFormula
from pyecsca.ec.point import Point


@public
class DoubleAndAddMultiplier(AccumulatorMultiplier, ScalarMultiplier, ABC):
    """
    Classic double and add scalar multiplication algorithm.

    .. note::
        This is an ABC, you should use the `LTRMultiplier` and `RTLMultiplier` classes.

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param always: Whether the double and add always method is used.
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
                DoubleAndAddMultiplier,
                super().__hash__(),
                self.direction,
                self.accumulation_order,
                self.always,
                self.complete,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, DoubleAndAddMultiplier):
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
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit}, direction={self.direction.name}, accumulation_order={self.accumulation_order.name}, always={self.always}, complete={self.complete})"

    def _ltr(self, scalar: int) -> Point:
        if self.complete:
            q = self._point
            r = copy(self._params.curve.neutral)
            top = self._params.order.bit_length() - 1
        else:
            q = copy(self._point)
            r = copy(self._point)
            top = scalar.bit_length() - 2
        for i in range(top, -1, -1):
            r = self._dbl(r)
            if scalar & (1 << i) != 0:
                r = self._accumulate(r, q)
            elif self.always:
                # dummy add
                self._accumulate(r, q)
        return r

    def _rtl(self, scalar: int) -> Point:
        q = self._point
        r = copy(self._params.curve.neutral)
        if self.complete:
            top = self._params.order.bit_length()
        else:
            top = scalar.bit_length()
        for _ in range(top):
            if scalar & 1 != 0:
                r = self._accumulate(r, q)
            elif self.always:
                # dummy add
                self._accumulate(r, q)
            # TODO: This double is unnecessary in the last iteration.
            q = self._dbl(q)
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


@public
class LTRMultiplier(DoubleAndAddMultiplier):
    """
    Classic double and add scalar multiplication algorithm, that scans the scalar left-to-right (msb to lsb).

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param always: Whether the double and add always method is used.
    :param accumulation_order: The order of accumulation of points.
    :param complete: Whether it starts processing at full order-bit-length.
    """

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        scl: Optional[ScalingFormula] = None,
        always: bool = False,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
        complete: bool = True,
        short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit,
            direction=ProcessingDirection.LTR,
            accumulation_order=accumulation_order,
            always=always,
            complete=complete,
            add=add,
            dbl=dbl,
            scl=scl,
        )


@public
class RTLMultiplier(DoubleAndAddMultiplier):
    """
    Classic double and add scalar multiplication algorithm, that scans the scalar right-to-left (lsb to msb).

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param always: Whether the double and add always method is used.
    :param accumulation_order: The order of accumulation of points.
    :param complete: Whether it starts processing at full order-bit-length.
    """

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        scl: Optional[ScalingFormula] = None,
        always: bool = False,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
        complete: bool = True,
        short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit,
            direction=ProcessingDirection.RTL,
            accumulation_order=accumulation_order,
            always=always,
            add=add,
            dbl=dbl,
            scl=scl,
            complete=complete,
        )


@public
class CoronMultiplier(ScalarMultiplier):
    """
    Coron's double and add resistant against SPA.

    From [CO2002]_.

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}

    def __init__(
        self,
        add: AdditionFormula,
        dbl: DoublingFormula,
        scl: Optional[ScalingFormula] = None,
        short_circuit: bool = True,
    ):
        super().__init__(short_circuit=short_circuit, add=add, dbl=dbl, scl=scl)

    def __hash__(self):
        return hash((CoronMultiplier, super().__hash__()))

    def __eq__(self, other):
        if not isinstance(other, CoronMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
        )

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            q = self._point
            p0 = copy(q)
            for i in range(scalar.bit_length() - 2, -1, -1):
                p0 = self._dbl(p0)
                p1 = self._add(p0, q)
                if scalar & (1 << i) != 0:
                    p0 = p1
            if "scl" in self.formulas:
                p0 = self._scl(p0)
            return action.exit(p0)
