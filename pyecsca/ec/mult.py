from copy import copy
from public import public
from typing import Mapping, Tuple, Optional, MutableMapping, Union

from pyecsca.ec.naf import naf, wnaf
from .context import Context
from .curve import EllipticCurve
from .formula import (Formula, AdditionFormula, DoublingFormula, ScalingFormula, LadderFormula,
                      NegationFormula, DifferentialAdditionFormula)
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

    def _dadd(self, start: Point, one: Point, other: Point) -> Point:
        if "dadd" not in self.formulas:
            raise NotImplementedError
        if one == self.curve.neutral:
            return copy(other)
        if other == self.curve.neutral:
            return copy(one)
        return self.context.execute(self.formulas["dadd"], start, one, other,
                                    **self.curve.parameters)[0]

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


@public
class LTRMultiplier(ScalarMultiplier):
    """
    Classic double and add scalar multiplication algorithm, that scans the scalar left-to-right (msb to lsb)

    The `always` parameter determines whether the double and add always method is used.
    """
    always: bool

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 scl: ScalingFormula = None,
                 ctx: Context = None, always: bool = False):
        super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)
        self.always = always

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        if scalar == 0:
            return copy(self.curve.neutral)
        q = self._init_multiply(point)
        r = copy(self.curve.neutral)
        for i in range(scalar.bit_length() - 1, -1, -1):
            r = self._dbl(r)
            if scalar & (1 << i) != 0:
                r = self._add(r, q)
            elif self.always:
                self._add(r, q)
        if "scl" in self.formulas:
            r = self._scl(r)
        return r


@public
class RTLMultiplier(ScalarMultiplier):
    """
    Classic double and add scalar multiplication algorithm, that scans the scalar right-to-left (lsb to msb)

    The `always` parameter determines whether the double and add always method is used.
    """
    always: bool

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 scl: ScalingFormula = None,
                 ctx: Context = None, always: bool = False):
        super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)
        self.always = always

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        if scalar == 0:
            return copy(self.curve.neutral)
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


class CoronMultiplier(ScalarMultiplier):
    """
    Coron's double and add resistant against SPA, from:

    Resistance against Differential Power Analysis for Elliptic Curve Cryptosystems

    https://link.springer.com/content/pdf/10.1007/3-540-48059-5_25.pdf
    """

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 scl: ScalingFormula = None, ctx: Context = None):
        super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)

    def multiply(self, scalar: int, point: Optional[Point] = None):
        q = self._init_multiply(point)
        p0 = copy(q)
        for i in range(scalar.bit_length() - 2, -1, -1):
            p0 = self._dbl(p0)
            p1 = self._add(p0, q)
            if scalar & (1 << i) != 0:
                p0 = p1
        if "scl" in self.formulas:
            p0 = self._scl(p0)
        return p0


@public
class LadderMultiplier(ScalarMultiplier):
    """
    Montgomery ladder multiplier, using a three input, two output ladder formula.
    """

    def __init__(self, curve: EllipticCurve, ladd: LadderFormula, scl: ScalingFormula = None,
                 ctx: Context = None):
        super().__init__(curve, ctx, ladd=ladd, scl=scl)

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        if scalar == 0:
            return copy(self.curve.neutral)
        q = self._init_multiply(point)
        p0 = copy(self.curve.neutral)
        p1 = copy(q)
        for i in range(scalar.bit_length() - 1, -1, -1):
            if scalar & (1 << i) == 0:
                p0, p1 = self._ladd(q, p0, p1)
            else:
                p1, p0 = self._ladd(q, p1, p0)
        if "scl" in self.formulas:
            p0 = self._scl(p0)
        return p0


@public
class SimpleLadderMultiplier(ScalarMultiplier):
    """
    Montgomery ladder multiplier, using addition and doubling formulas.
    """
    _differential: bool = False

    def __init__(self, curve: EllipticCurve,
                 add: Union[AdditionFormula, DifferentialAdditionFormula], dbl: DoublingFormula,
                 scl: ScalingFormula = None, ctx: Context = None):
        if isinstance(add, AdditionFormula):
            super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)
        elif isinstance(add, DifferentialAdditionFormula):
            super().__init__(curve, ctx, dadd=add, dbl=dbl, scl=scl)
            self._differential = True
        else:
            raise ValueError

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        if scalar == 0:
            return copy(self.curve.neutral)
        q = self._init_multiply(point)
        p0 = copy(self.curve.neutral)
        p1 = copy(q)
        for i in range(scalar.bit_length() - 1, -1, -1):
            if scalar & (1 << i) == 0:
                if self._differential:
                    p1 = self._dadd(q, p0, p1)
                else:
                    p1 = self._add(p0, p1)
                p0 = self._dbl(p0)
            else:
                if self._differential:
                    p0 = self._dadd(q, p0, p1)
                else:
                    p0 = self._add(p0, p1)
                p1 = self._dbl(p1)
        if "scl" in self.formulas:
            p0 = self._scl(p0)
        return p0


@public
class BinaryNAFMultiplier(ScalarMultiplier):
    """
    Binary NAF (Non Adjacent Form) multiplier, left-to-right.
    """
    _point_neg: Point

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 neg: NegationFormula, scl: ScalingFormula = None, ctx: Context = None):
        super().__init__(curve, ctx, add=add, dbl=dbl, neg=neg, scl=scl)

    def init(self, point: Point):
        super().init(point)
        self._point_neg = self._neg(point)

    def multiply(self, scalar: int, point: Optional[Point] = None) -> Point:
        if scalar == 0:
            return copy(self.curve.neutral)
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


@public
class WindowNAFMultiplier(ScalarMultiplier):
    """
    Window NAF (Non Adjacent Form) multiplier, left-to-right.
    """
    _points: MutableMapping[int, Point]
    _points_neg: MutableMapping[int, Point]
    _precompute_neg: bool = False
    _width: int

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 neg: NegationFormula, width: int, scl: ScalingFormula = None, ctx: Context = None,
                 precompute_negation: bool = False):
        super().__init__(curve, ctx, add=add, dbl=dbl, neg=neg, scl=scl)
        self._width = width
        self._precompute_neg = precompute_negation

    def init(self, point: Point):
        self._point = point
        self._points = {}
        self._points_neg = {}
        current_point = point
        double_point = self._dbl(point)
        for i in range(1, (self._width + 1) // 2 + 1):
            self._points[2 ** i - 1] = current_point
            if self._precompute_neg:
                self._points_neg[2 ** i - 1] = self._neg(current_point)
            current_point = self._add(current_point, double_point)

    def multiply(self, scalar: int, point: Optional[Point] = None):
        if scalar == 0:
            return copy(self.curve.neutral)
        self._init_multiply(point)
        naf = wnaf(scalar, self._width)
        q = copy(self.curve.neutral)
        for val in naf:
            q = self._dbl(q)
            if val > 0:
                q = self._add(q, self._points[val])
            elif val < 0:
                if self._precompute_neg:
                    neg = self._points_neg[-val]
                else:
                    neg = self._neg(self._points[-val])
                q = self._add(q, neg)
        if "scl" in self.formulas:
            q = self._scl(q)
        return q
