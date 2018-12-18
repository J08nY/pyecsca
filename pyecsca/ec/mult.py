from copy import copy
from typing import Mapping, Tuple, Optional, MutableMapping

from pyecsca.ec.naf import naf, wnaf
from .context import Context
from .curve import EllipticCurve
from .formula import (Formula, AdditionFormula, DoublingFormula, ScalingFormula, LadderFormula,
                      NegationFormula)
from .point import Point


class ScalarMultiplier(object):
    curve: EllipticCurve
    formulas: Mapping[str, Formula]
    context: Context
    _point: Point = None

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

    def _ladd(self, start: Point, to_dbl: Point, to_add: Point) -> Tuple[Point, ...]:
        if "ladd" not in self.formulas:
            raise NotImplementedError
        return self.context.execute(self.formulas["ladd"], start, to_dbl, to_add,
                                    **self.curve.parameters)

    def _neg(self, point: Point) -> Point:
        if "neg" not in self.formulas:
            raise NotImplementedError
        return self.context.execute(self.formulas["neg"], point, **self.curve.parameters)[0]

    def init(self, point: Point):
        self._point = point

    def _init_multiply(self, point: Optional[Point]) -> Point:
        if point is None:
            if self._point is None:
                raise ValueError
        else:
            if self._point != point:
                self.init(point)
        return self._point

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        raise NotImplementedError


class LTRMultiplier(ScalarMultiplier):
    always: bool

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 scl: ScalingFormula = None,
                 ctx: Context = None, always: bool = False):
        super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)
        self.always = always

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        q = self._init_multiply(point)
        r = copy(self.curve.neutral)
        for i in range(scalar.bit_length(), -1, -1):
            r = self._dbl(r)
            if scalar & (1 << i) != 0:
                r = self._add(r, q)
            elif self.always:
                self._add(r, q)
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

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        q = self._init_multiply(point)
        r = copy(self.curve.neutral)
        while scalar > 0:
            if scalar & 1 != 0:
                r = self._add(r, q)
            elif self.always:
                self._add(r, q)
            q = self._dbl(q)
            scalar >>= 1
        if "scl" in self.formulas:
            r = self._scl(r)
        return r


class LadderMultiplier(ScalarMultiplier):

    def __init__(self, curve: EllipticCurve, ladd: LadderFormula, scl: ScalingFormula = None,
                 ctx: Context = None):
        super().__init__(curve, ctx, ladd=ladd, scl=scl)

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        q = self._init_multiply(point)
        p0 = copy(q)
        p1 = self._ladd(self.curve.neutral, q, q)[1]
        for i in range(scalar.bit_length(), -1, -1):
            if scalar & i != 0:
                p0, p1 = self._ladd(q, p1, p0)
            else:
                p0, p1 = self._ladd(q, p0, p1)
        if "scl" in self.formulas:
            p0 = self._scl(p0)
        return p0


class BinaryNAFMultiplier(ScalarMultiplier):
    _point_neg: Point

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 neg: NegationFormula, scl: ScalingFormula = None, ctx: Context = None):
        super().__init__(curve, ctx, add=add, dbl=dbl, neg=neg, scl=scl)

    def init(self, point: Point):
        super().init(point)
        self._point_neg = self._neg(point)

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        self._init_multiply(point)
        bnaf = naf(scalar)
        q = copy(self.curve.neutral)
        for val in bnaf:
            q = self._dbl(q)
            if val == 1:
                q = self._add(q, self._point)
            if val == -1:
                q = self._add(q, self._point_neg)
        if "scl" in self.formulas:
            q = self._scl(q)
        return q


class WindowNAFMultiplier(ScalarMultiplier):
    _points: MutableMapping[int, Point]
    _width: int

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 neg: NegationFormula, width: int, scl: ScalingFormula = None, ctx: Context = None):
        super().__init__(curve, ctx, add=add, dbl=dbl, neg=neg, scl=scl)
        self._width = width

    def init(self, point: Point):
        self._point = point
        self._points = {}
        current_point = point
        double_point = self._dbl(point)
        for i in range(1, (self._width + 1) // 2 + 1):
            self._points[2 ** i - 1] = current_point
            current_point = self._add(current_point, double_point)

    def multiply(self, scalar: int, point: Optional[Point] = None):
        self._init_multiply(point)
        naf = wnaf(scalar, self._width)
        q = copy(self.curve.neutral)
        for val in naf:
            q = self._dbl(q)
            if val > 0:
                q = self._add(q, self._points[val])
            elif val < 0:
                neg = self._neg(self._points[-val])
                q = self._add(q, neg)
        if "scl" in self.formulas:
            q = self._scl(q)
        return q
