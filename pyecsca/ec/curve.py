from typing import Mapping

from .coordinates import CoordinateModel
from .model import CurveModel
from .point import Point


class EllipticCurve(object):
    model: CurveModel
    coordinate_model: CoordinateModel
    parameters: Mapping[str, int]
    neutral: Point

    def __init__(self, model: CurveModel, coordinate_model: CoordinateModel,
                 parameters: Mapping[str, int], neutral: Point):
        if coordinate_model not in model.coordinates.values():
            raise ValueError
        if set(model.parameter_names).symmetric_difference(parameters.keys()):
            raise ValueError
        if neutral.coordinate_model != coordinate_model:
            raise ValueError
        self.model = model
        self.coordinate_model = coordinate_model
        self.parameters = dict(parameters)
        self.neutral = neutral

    def is_on_curve(self, point: Point) -> bool:
        pass

    def is_neutral(self, point: Point) -> bool:
        return self.neutral == point

    def __repr__(self):
        params = ", ".join((f"{key}={val}" for key, val in self.parameters.items()))
        return f"EllipticCurve([{params}] on {self.model} using {self.coordinate_model})"
