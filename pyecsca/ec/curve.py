from typing import Type, Mapping

from .point import Point
from .coordinates import CoordinateModel
from .model import CurveModel


class EllipticCurve(object):
    model: Type[CurveModel]
    coordinate_model: CoordinateModel
    parameters: Mapping[str, int]
    neutral: Point

    def __init__(self, model: Type[CurveModel], coordinate_model: CoordinateModel,
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
