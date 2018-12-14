from copy import copy
from typing import Mapping

from .context import Context
from .curve import EllipticCurve
from .formula import Formula, AdditionFormula, DoublingFormula, ScalingFormula
from .point import Point


class ScalarMultiplier(object):
    curve: EllipticCurve
    formulas: Mapping[str, Formula]
    context: Context

    def __init__(self, curve: EllipticCurve, ctx: Context = None, **formulas: Formula):
        for formula in formulas.values():
            if formula is not None and formula.coordinate_model is not curve.coordinate_model:
                raise ValueError
        self.curve = curve
        if ctx:
            self.context = ctx
        else:
            self.context = Context()
        self.formulas = dict(formulas)

    def _add(self, one: Point, other: Point) -> Point:
        if "add" not in self.formulas:
            raise NotImplementedError
        if one == self.curve.neutral:
            return copy(other)
        if other == self.curve.neutral:
            return copy(one)
        return self.context.execute(self.formulas["add"], one, other, **self.curve.parameters)

    def _dbl(self, point: Point) -> Point:
        if "dbl" not in self.formulas:
            raise NotImplementedError
        if point == self.curve.neutral:
            return copy(point)
        return self.context.execute(self.formulas["dbl"], point, **self.curve.parameters)

    def _scl(self, point: Point) -> Point:
        if "scl" not in self.formulas:
            raise NotImplementedError
        return self.context.execute(self.formulas["scl"], point, **self.curve.parameters)

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
