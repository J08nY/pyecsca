from copy import copy
from typing import Mapping, Tuple, Optional

from .context import Context
from .curve import EllipticCurve
from .formula import Formula, AdditionFormula, DoublingFormula, ScalingFormula, LadderFormula
from .point import Point


class ScalarMultiplier(object):
    curve: EllipticCurve
    formulas: Mapping[str, Formula]
    context: Context

    def __init__(self, curve: EllipticCurve, ctx: Context = None, **formulas: Optional[Formula]):
        for formula in formulas.values():
            if formula is not None and formula.coordinate_model is not curve.coordinate_model:
                raise ValueError
        self.curve = curve
        if ctx:
            self.context = ctx
        else:
            self.context = Context()
        self.formulas = dict(filter(lambda pair: pair[1] is not None, formulas.items()))

    def _add(self, one: Point, other: Point) -> Point:
        if "add" not in self.formulas:
            raise NotImplementedError
        if one == self.curve.neutral:
            return copy(other)
        if other == self.curve.neutral:
            return copy(one)
        return self.context.execute(self.formulas["add"], one, other, **self.curve.parameters)[0]

    def _dbl(self, point: Point) -> Point:
        if "dbl" not in self.formulas:
            raise NotImplementedError
        if point == self.curve.neutral:
            return copy(point)
        return self.context.execute(self.formulas["dbl"], point, **self.curve.parameters)[0]

    def _scl(self, point: Point) -> Point:
        if "scl" not in self.formulas:
            raise NotImplementedError
        return self.context.execute(self.formulas["scl"], point, **self.curve.parameters)[0]

    def _ladd(self, start: Point, to_dbl: Point, to_add: Point) -> Tuple[Point, Point]:
        if "ladd" not in self.formulas:
            raise NotImplementedError
        return self.context.execute(self.formulas["ladd"], start, to_dbl, to_add,
                                    **self.curve.parameters)

    def multiply(self, scalar: int, point: Point) -> Point:
        raise NotImplementedError


class LTRMultiplier(ScalarMultiplier):
    always: bool

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 scl: ScalingFormula = None,
                 ctx: Context = None, always: bool = False):
        super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)
        self.always = always

    def multiply(self, scalar: int, point: Point) -> Point:
        r = copy(self.curve.neutral)
        for i in range(scalar.bit_length(), -1, -1):
            r = self._dbl(r)
            if scalar & (1 << i) != 0:
                r = self._add(r, point)
            elif self.always:
                self._add(r, point)
        if "scl" in self.formulas:
            r = self._scl(r)
        return r


class RTLMultiplier(ScalarMultiplier):
    always: bool

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 scl: ScalingFormula = None,
                 ctx: Context = None, always: bool = False):
        super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)
        self.always = always

    def multiply(self, scalar: int, point: Point) -> Point:
        r = copy(self.curve.neutral)
        while scalar > 0:
            if scalar & 1 != 0:
                r = self._add(r, point)
            elif self.always:
                self._add(r, point)
            point = self._dbl(point)
            scalar >>= 1
        if "scl" in self.formulas:
            r = self._scl(r)
        return r


class LadderMultiplier(ScalarMultiplier):

    def __init__(self, curve: EllipticCurve, ladd: LadderFormula, scl: ScalingFormula = None,
                 ctx: Context = None):
        super().__init__(curve, ctx, ladd=ladd, scl=scl)

    def multiply(self, scalar: int, point: Point) -> Point:
        p0 = copy(point)
        p1 = self._ladd(self.curve.neutral, point, point)[1]
        for i in range(scalar.bit_length(), -1, -1):
            if scalar & i != 0:
                p0, p1 = self._ladd(point, p1, p0)
            else:
                p0, p1 = self._ladd(point, p0, p1)
        if "scl" in self.formulas:
            p0 = self._scl(p0)
        return p0
