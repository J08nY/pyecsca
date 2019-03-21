from copy import copy
from public import public
from typing import Mapping

from .coordinates import CoordinateModel, AffineCoordinateModel
from .mod import Mod
from .op import CodeOp


@public
class Point(object):
    coordinate_model: CoordinateModel
    coords: Mapping[str, Mod]

    def __init__(self, model: CoordinateModel, **coords: Mod):
        if not set(model.variables) == set(coords.keys()):
            raise ValueError
        self.coordinate_model = model
        self.coords = coords

    def to_affine(self):
        if isinstance(self.coordinate_model, AffineCoordinateModel):
            return copy(self)
        ops = set()
        for s in self.coordinate_model.satisfying:
            try:
                ops.add(CodeOp(s))
            except:
                pass
        affine_model = AffineCoordinateModel(self.coordinate_model.curve_model)
        # TODO: just fill in with undefined
        if not set(map(lambda x: x.result, ops)).issuperset(affine_model.variables):
            raise NotImplementedError
        result = {}
        for op in ops:
            result[op.result] = op(**self.coords)
        return Point(affine_model, **result)

    @staticmethod
    def from_affine(affine_point):
        # TODO
        pass

    def equals(self, other):
        if not isinstance(other, Point):
            return False
        if self.coordinate_model.curve_model != other.coordinate_model.curve_model:
            return False
        return self.to_affine() == other.to_affine()

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        if self.coordinate_model != other.coordinate_model:
            return False
        return self.coords == other.coords

    def __str__(self):
        args = ", ".join([f"{key}={val}" for key, val in self.coords.items()])
        return f"[{args}]"

    def __repr__(self):
        return f"Point([{str(self)}] in {self.coordinate_model})"


@public
class InfinityPoint(Point):

    def __init__(self, model: CoordinateModel):
        self.coordinate_model = model
        self.coords = {}

    def to_affine(self):
        return InfinityPoint(AffineCoordinateModel(self.coordinate_model.curve_model))

    @staticmethod
    def from_affine(affine_point):
        raise NotImplementedError

    def equals(self, other):
        return self == other

    def __eq__(self, other):
        if type(other) is not InfinityPoint:
            return False
        else:
            return self.coordinate_model == other.coordinate_model

    def __str__(self):
        return "Infinity"

    def __repr__(self):
        return f"InfinityPoint({self.coordinate_model})"
