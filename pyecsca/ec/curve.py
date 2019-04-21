from public import public
from typing import MutableMapping, Union

from .coordinates import CoordinateModel
from .mod import Mod
from .model import CurveModel
from .point import Point


@public
class EllipticCurve(object):
    model: CurveModel
    coordinate_model: CoordinateModel
    prime: int
    parameters: MutableMapping[str, Mod]
    neutral: Point

    def __init__(self, model: CurveModel, coordinate_model: CoordinateModel,
                 prime: int, parameters: MutableMapping[str, Union[Mod, int]], neutral: Point):
        # TODO: Add base_point arg, order arg, cofactor arg.
        if coordinate_model not in model.coordinates.values():
            raise ValueError
        if set(model.parameter_names).symmetric_difference(parameters.keys()):
            raise ValueError
        if neutral.coordinate_model != coordinate_model:
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
        self.neutral = neutral

    def is_on_curve(self, point: Point) -> bool:
        if point.coordinate_model != self.coordinate_model:
            return False
        loc = {**self.parameters, **point.to_affine().coords}
        return eval(compile(self.model.equation, "", mode="eval"), loc)

    def is_neutral(self, point: Point) -> bool:
        return self.neutral == point

    def __repr__(self):
        params = ", ".join((f"{key}={val}" for key, val in self.parameters.items()))
        return f"EllipticCurve([{params}] on {self.model} using {self.coordinate_model})"
