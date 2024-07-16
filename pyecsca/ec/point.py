"""Provides a :py:class:`.Point` class and a special :py:class:`.InfinityPoint` class for the point at infinity."""
from copy import copy
from typing import Mapping, TYPE_CHECKING

from public import public

from pyecsca.ec.context import ResultAction
from pyecsca.ec.coordinates import AffineCoordinateModel, CoordinateModel
from pyecsca.ec.mod import Mod, Undefined, mod
from pyecsca.ec.op import CodeOp


if TYPE_CHECKING:
    from .curve import EllipticCurve


@public
class CoordinateMappingAction(ResultAction):
    """A mapping of a point from one coordinate system to another one, usually one is an affine one."""

    model_from: CoordinateModel
    model_to: CoordinateModel
    point: "Point"

    def __init__(
        self, model_from: CoordinateModel, model_to: CoordinateModel, point: "Point"
    ):
        super().__init__()
        self.model_from = model_from
        self.model_to = model_to
        self.point = point

    def __repr__(self):
        return f"{self.__class__.__name__}(from={self.model_from}, to={self.model_to}, {self.point})"


@public
class Point:
    """A point with coordinates in a coordinate model."""

    coordinate_model: CoordinateModel
    coords: Mapping[str, Mod]
    field: int

    def __init__(self, model: CoordinateModel, **coords: Mod):
        if not set(model.variables) == set(coords.keys()):
            raise ValueError(
                f"Wrong coordinate values for coordinate model, expected {model.variables} got {coords.keys()}."
            )
        self.coordinate_model = model
        self.coords = coords
        field = None
        for value in self.coords.values():
            if field is None:
                field = value.n
            else:
                if field != value.n:
                    raise ValueError(
                        f"Mismatched coordinate field of definition, {field} vs {value.n}."
                    )
        self.field = field if field is not None else 0

    def __getattribute__(self, name):
        # Do the magic such that point.X1 works!
        if "coords" in super().__getattribute__("__dict__"):
            coords = super().__getattribute__("coords")
            if name in coords:
                return coords[name]
        return super().__getattribute__(name)

    def to_affine(self) -> "Point":
        """Convert this point into the affine coordinate model, if possible."""
        affine_model = AffineCoordinateModel(self.coordinate_model.curve_model)
        with CoordinateMappingAction(
            self.coordinate_model, affine_model, self
        ) as action:
            if isinstance(self.coordinate_model, AffineCoordinateModel):
                return action.exit(copy(self))
            ops = []
            for s in self.coordinate_model.satisfying:
                try:
                    ops.append(CodeOp(s))
                except Exception:
                    pass
            result_variables = set(map(lambda x: x.result, ops))
            if not result_variables.issuperset(affine_model.variables):
                raise NotImplementedError(
                    f"Coordinate model does have affine mapping function ({result_variables})"
                )
            result = {}
            locls = {**self.coords}
            for op in ops:
                try:
                    locls[op.result] = op(**locls)
                except NameError as e:
                    if op.result in affine_model.variables:
                        raise e
                    else:
                        continue
                if op.result in affine_model.variables:
                    result[op.result] = locls[op.result]
            return action.exit(Point(affine_model, **result))

    def to_model(
        self,
        coordinate_model: CoordinateModel,
        curve: "EllipticCurve",
        randomized: bool = False,
    ) -> "Point":
        """Convert an affine point into a given coordinate model, if possible."""
        if not isinstance(self.coordinate_model, AffineCoordinateModel):
            raise ValueError
        with CoordinateMappingAction(
            self.coordinate_model, coordinate_model, self
        ) as action:
            if isinstance(coordinate_model, AffineCoordinateModel):
                return action.exit(Point(coordinate_model, **self.coords))
            ops = []
            for s in coordinate_model.tosystem:
                try:
                    ops.append(CodeOp(s))
                except Exception:
                    pass
            locls = {**self.coords, **curve.parameters}
            for op in ops:
                try:
                    locls[op.result] = op(**locls)
                except Exception:
                    continue
            result = {}
            for var in coordinate_model.variables:
                if var in locls:
                    result[var] = (
                        mod(locls[var], curve.prime)  # type: ignore
                        if not isinstance(locls[var], Mod)
                        else locls[var]
                    )
                else:
                    raise NotImplementedError
            if randomized:
                lmbd = Mod.random(curve.prime)
                for var, value in result.items():
                    result[var] = value * (lmbd ** coordinate_model.homogweights[var])
            return action.exit(Point(coordinate_model, **result))

    def equals_affine(self, other: "Point") -> bool:
        """Test whether this point is equal to :paramref:`~.equals_affine.other` irrespective of the coordinate model (in the affine sense)."""
        if not isinstance(other, Point) or isinstance(other, InfinityPoint):
            return False
        if self.coordinate_model.curve_model != other.coordinate_model.curve_model:
            return False
        return self.to_affine() == other.to_affine()

    def equals_scaled(self, other: "Point") -> bool:
        """
        Test whether this point is equal to :paramref:`~.equals_scaled.other` using the "z" scaling formula.

        The "z" scaling formula maps the projective class to a single representative.

        :param other: The point to compare
        :raises ValueError: If the "z" formula is not available for the coordinate system.
        :return: Whether the points are equal.
        """
        if not isinstance(other, Point) or isinstance(other, InfinityPoint):
            return False
        if self.coordinate_model.curve_model != other.coordinate_model.curve_model:
            return False
        if "z" in self.coordinate_model.formulas:
            formula = self.coordinate_model.formulas["z"]
            self_mapped = formula(self.field, self)
            other_mapped = formula(self.field, other)
            return self_mapped == other_mapped
        else:
            raise ValueError("No scaling formula available.")

    def equals(self, other: "Point") -> bool:
        """Test whether this point is equal to `other` irrespective of the coordinate model (in the affine sense)."""
        return self.equals_affine(other)

    def __iter__(self):
        for k in sorted(self.coords.keys()):
            yield self.coords[k]

    def __len__(self):
        return len(self.coords)

    def __bytes__(self):
        res = b"\x04"
        for k in sorted(self.coords.keys()):
            res += bytes(self.coords[k])
        return res

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        if self.coordinate_model != other.coordinate_model:
            return False
        return self.coords == other.coords

    def __hash__(self):
        return hash(
            (
                self.coordinate_model,
                tuple(self.coords.keys()),
                tuple(self.coords.values()),
            )
        )

    def __str__(self):
        args = ", ".join([f"{key}={val}" for key, val in self.coords.items()])
        return f"[{args}]"

    def __repr__(self):
        return f"Point({str(self)} in {self.coordinate_model})"


@public
class InfinityPoint(Point):
    """A point at infinity."""

    def __init__(self, model: CoordinateModel):
        coords = {key: Undefined() for key in model.variables}
        super().__init__(model, **coords)

    def to_affine(self) -> "InfinityPoint":
        return InfinityPoint(AffineCoordinateModel(self.coordinate_model.curve_model))

    def to_model(
        self,
        coordinate_model: CoordinateModel,
        curve: "EllipticCurve",
        randomized: bool = False,
    ) -> "InfinityPoint":
        return InfinityPoint(coordinate_model)

    def equals_affine(self, other: "Point") -> bool:
        return self == other

    def equals_scaled(self, other: "Point") -> bool:
        return self == other

    def equals(self, other: "Point") -> bool:
        return self == other

    def __iter__(self):
        yield from ()

    def __len__(self):
        return 0

    def __bytes__(self):
        return b"\x00"

    def __eq__(self, other):
        if type(other) is not InfinityPoint:
            return False
        else:
            return self.coordinate_model == other.coordinate_model

    def __hash__(self):
        return hash((self.coordinate_model, 0))

    def __str__(self):
        return "Infinity"

    def __repr__(self):
        return f"InfinityPoint({self.coordinate_model})"
