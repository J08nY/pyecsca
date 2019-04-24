from copy import copy
from typing import Mapping, Any

from public import public

from .coordinates import CoordinateModel, AffineCoordinateModel
from .mod import Mod, Undefined
from .op import CodeOp


@public
class Point(object):
    """A point with coordinates in a coordinate model."""
    coordinate_model: CoordinateModel
    coords: Mapping[str, Mod]

    def __init__(self, model: CoordinateModel, **coords: Mod):
        if not set(model.variables) == set(coords.keys()):
            raise ValueError
        self.coordinate_model = model
        self.coords = coords

    def __getattribute__(self, name):
        if "coords" in super().__getattribute__("__dict__"):
            coords = super().__getattribute__("coords")
            if name in coords:
                return coords[name]
        return super().__getattribute__(name)

    def to_affine(self) -> "Point":
        """Convert this point into the affine coordinate model, if possible."""
        if isinstance(self.coordinate_model, AffineCoordinateModel):
            return copy(self)
        ops = set()
        for s in self.coordinate_model.satisfying:
            try:
                ops.add(CodeOp(s))
            except:
                pass
        affine_model = AffineCoordinateModel(self.coordinate_model.curve_model)
        result_variables = set(map(lambda x: x.result, ops))
        if not result_variables.issuperset(affine_model.variables):
            raise NotImplementedError
        result = {}
        for op in ops:
            if op.result not in affine_model.variables:
                continue
            result[op.result] = op(**self.coords)
        return Point(affine_model, **result)

    @staticmethod
    def from_affine(coordinate_model: CoordinateModel, affine_point: "Point") -> "Point":
        """Convert an affine point into a given coordinate model, if possible."""
        if not isinstance(affine_point.coordinate_model, AffineCoordinateModel):
            raise ValueError
        result = {}
        n = affine_point.coords["x"].n
        for var in coordinate_model.variables:  #  XXX: This just works for the stuff currently in EFD.
            if var == "X":
                result[var] = affine_point.coords["x"]
            elif var == "Y":
                result[var] = affine_point.coords["y"]
            elif var.startswith("Z"):
                result[var] = Mod(1, n)
            elif var == "T":
                result[var] = Mod(affine_point.coords["x"] * affine_point.coords["y"], n)
            else:
                raise NotImplementedError
        return Point(coordinate_model, **result)

    def equals(self, other: Any) -> bool:
        """Test whether this point is equal to `other` irrespective of the coordinate model (in the affine sense)."""
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
    """A point at infinity."""

    def __init__(self, model: CoordinateModel):
        coords = {key: Undefined() for key in model.variables}
        super().__init__(model, **coords)

    def to_affine(self) -> "InfinityPoint":
        return InfinityPoint(AffineCoordinateModel(self.coordinate_model.curve_model))

    @staticmethod
    def from_affine(coordinate_model: CoordinateModel, affine_point: "Point") -> "InfinityPoint":
        raise NotImplementedError

    def equals(self, other) -> bool:
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
