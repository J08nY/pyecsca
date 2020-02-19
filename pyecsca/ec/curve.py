from ast import Module
from typing import MutableMapping, Union, List

from public import public

from .coordinates import CoordinateModel, AffineCoordinateModel
from .mod import Mod
from .model import CurveModel
from .point import Point


@public
class EllipticCurve(object):
    model: CurveModel
    coordinate_model: CoordinateModel
    prime: int
    parameters: MutableMapping[str, Mod]

    def __init__(self, model: CurveModel, coordinate_model: CoordinateModel,
                 prime: int, parameters: MutableMapping[str, Union[Mod, int]]):
        if coordinate_model not in model.coordinates.values():
            raise ValueError
        if set(model.parameter_names).symmetric_difference(parameters.keys()):
            raise ValueError
        self.model = model
        self.coordinate_model = coordinate_model
        self.prime = prime
        self.parameters = {}
        for name, value in parameters.items():
            if isinstance(value, Mod):
                if value.n != prime:
                    raise ValueError
            else:
                value = Mod(value, prime)
            self.parameters[name] = value

    def _execute_base_formulas(self, formulas: List[Module], *points: Point) -> Point:
        for point in points:
            if point.coordinate_model.curve_model != self.model:
                raise ValueError
            if not isinstance(point.coordinate_model, AffineCoordinateModel):
                raise ValueError
        locals = {var + str(i + 1): point.coords[var]
                  for i, point in enumerate(points) for var in point.coords}
        locals.update(self.parameters)
        for line in formulas:
            exec(compile(line, "", mode="exec"), None, locals)
        return Point(AffineCoordinateModel(self), x=locals["x"], y=locals["y"])

    def affine_add(self, one: Point, other: Point) -> Point:
        return self._execute_base_formulas(self.model.base_addition, one, other)

    def affine_double(self, one: Point) -> Point:
        return self._execute_base_formulas(self.model.base_doubling, one)

    def affine_negate(self, one: Point) -> Point:
        return self._execute_base_formulas(self.model.base_negation, one)

    @property
    def neutral_is_affine(self):
        return bool(self.model.base_neutral)

    def is_on_curve(self, point: Point) -> bool:
        if point.coordinate_model.curve_model != self.model:
            return False
        loc = {**self.parameters, **point.to_affine().coords}
        return eval(compile(self.model.equation, "", mode="eval"), loc)

    def __eq__(self, other):
        if not isinstance(other, EllipticCurve):
            return False
        return self.model == other.model and self.coordinate_model == other.coordinate_model and self.prime == other.prime and self.parameters == other.parameters

    def __str__(self):
        return "EllipticCurve"

    def __repr__(self):
        params = ", ".join((f"{key}={val}" for key, val in self.parameters.items()))
        return f"{self.__class__.__name__}([{params}] on {self.model} using {self.coordinate_model})"
