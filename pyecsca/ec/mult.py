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
        pass


class RTLMultiplier(ScalarMultiplier):
    always: bool
    scale: bool

    def __init__(self, curve: EllipticCurve, add: AdditionFormula, dbl: DoublingFormula,
                 scl: ScalingFormula = None,
                 ctx: Context = None, scale: bool = True, always: bool = False):
        super().__init__(curve, ctx, add=add, dbl=dbl, scl=scl)
        self.always = always
        self.scale = scale

    def multiply(self, scalar: int, point: Point) -> Point:
        q = copy(point)
        r = copy(self.curve.neutral)
        while scalar > 0:
            q = self.context.execute(self.formulas["dbl"], q, **self.curve.parameters)
            if self.always:
                tmp = self.context.execute(self.formulas["add"], r, q, **self.curve.parameters)
            else:
                if r == self.curve.neutral:
                    tmp = copy(q)
                else:
                    tmp = self.context.execute(self.formulas["add"], r, q, **self.curve.parameters)
            if scalar & 1 != 0:
                r = tmp
            scalar >>= 1
        if self.scale:
            r = self.context.execute(self.formulas["scl"], r, **self.curve.parameters)
        return r
