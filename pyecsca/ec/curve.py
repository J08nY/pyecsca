from ast import Module
from copy import copy
from typing import MutableMapping, Union, List, Optional

from public import public

from .coordinates import CoordinateModel, AffineCoordinateModel
from .mod import Mod
from .model import CurveModel
from .point import Point, InfinityPoint


@public
class EllipticCurve(object):
    """An elliptic curve."""
    model: CurveModel
    """The model of the curve."""
    coordinate_model: CoordinateModel
    """The coordinate system of the curve."""
    prime: int
    """The prime specifying the base prime field of the curve."""
    parameters: MutableMapping[str, Mod]
    """The values of the parameters defining the curve, these cover the curve model and coordinate system parameters."""
    neutral: Point
    """The neutral point on the curve."""

    def __init__(self, model: CurveModel, coordinate_model: CoordinateModel,
                 prime: int, neutral: Point, parameters: MutableMapping[str, Union[Mod, int]]):
        if coordinate_model not in model.coordinates.values() and not isinstance(coordinate_model, AffineCoordinateModel):
            raise ValueError
        if set(model.parameter_names).union(coordinate_model.parameters).symmetric_difference(parameters.keys()):
            raise ValueError
        self.model = model
        self.coordinate_model = coordinate_model
        self.prime = prime
        self.parameters = {}
        for name, value in parameters.items():
            if isinstance(value, Mod):
                if value.n != prime:
                    raise ValueError(f"Parameter {name} has wrong modulus.")
            else:
                value = Mod(value, prime)
            self.parameters[name] = value
        self.neutral = neutral

    def _execute_base_formulas(self, formulas: List[Module], *points: Point) -> Point:
        for point in points:
            if not isinstance(point.coordinate_model, AffineCoordinateModel):
                raise ValueError("Coordinate model of point is not affine.")
            if point.coordinate_model.curve_model != self.model:
                raise ValueError("Curve model of point does not match the curve.")
        locls = {var + str(i + 1): point.coords[var]
                 for i, point in enumerate(points) for var in point.coords}
        locls.update(self.parameters)
        for line in formulas:
            exec(compile(line, "", mode="exec"), None, locls)
        if not isinstance(locls["x"], Mod):
            locls["x"] = Mod(locls["x"], self.prime)
        if not isinstance(locls["y"], Mod):
            locls["y"] = Mod(locls["y"], self.prime)
        return Point(AffineCoordinateModel(self.model), x=locls["x"], y=locls["y"])

    def affine_add(self, one: Point, other: Point) -> Point:
        """
        Add two affine points using the affine addition formula.
        Handles the case of point at infinity gracefully.

        :param one: One point.
        :param other: Another point.
        :return: The addition of the two points.
        """
        if isinstance(one, InfinityPoint):
            return other
        if isinstance(other, InfinityPoint):
            return one
        if one == other:
            return self.affine_double(one)
        return self._execute_base_formulas(self.model.base_addition, one, other)

    def affine_double(self, one: Point) -> Point:
        """
        Double an affine point using the affine doubling formula.
        Handles the case of point at infinity gracefully.

        :param one: A point.
        :return: The doubling of the point.
        """
        if isinstance(one, InfinityPoint):
            return one
        return self._execute_base_formulas(self.model.base_doubling, one)

    def affine_negate(self, one: Point) -> Point:
        """
        Negate an affine point using the affine negation formula.
        Handles the case of point at infinity gracefully.

        :param one: A point.
        :return: The negation of the point.
        """
        if isinstance(one, InfinityPoint):
            return one
        return self._execute_base_formulas(self.model.base_negation, one)

    def affine_multiply(self, point: Point, scalar: int) -> Point:
        """
        Multiply an affine point by a scalar using the affine doubling and addition formulas.
        Handles the case of point at infinity gracefully.

        :param point: The point to multiply.
        :param scalar: The scalar to use.
        :return: The scalar multiplication of `point`.
        """
        if isinstance(point, InfinityPoint):
            return point
        if not isinstance(point.coordinate_model, AffineCoordinateModel):
            raise ValueError("Coordinate model of point is not affine.")
        if point.coordinate_model.curve_model != self.model:
            raise ValueError("Curve model of point does not match the curve.")
        q = copy(point)
        r = copy(point)

        for i in range(scalar.bit_length() - 2, -1, -1):
            r = self.affine_double(r)
            if scalar & (1 << i) != 0:
                r = self.affine_add(r, q)
        return r

    @property
    def affine_neutral(self) -> Optional[Point]:
        """
        Get the neutral point in affine form, if it has one, otherwise `None`.

        :return: The affine neutral point or `None`.
        """
        if not self.neutral_is_affine:
            return None
        locls = {**self.parameters}
        for line in self.model.base_neutral:
            exec(compile(line, "", mode="exec"), None, locls)
        if not isinstance(locls["x"], Mod):
            locls["x"] = Mod(locls["x"], self.prime)
        if not isinstance(locls["y"], Mod):
            locls["y"] = Mod(locls["y"], self.prime)
        return Point(AffineCoordinateModel(self.model), x=locls["x"], y=locls["y"])

    @property
    def neutral_is_affine(self):
        """Whether the neutral point is an affine point."""
        return bool(self.model.base_neutral)

    def is_neutral(self, point: Point) -> bool:
        """Check whether the point is the neutral point.

        :param point: The point to test.
        :return: Whether it is the neutral point.
        """
        return self.neutral == point

    def is_on_curve(self, point: Point) -> bool:
        """
        Check whether the point is on the curve.

        :param point: The point to test.
        :return: Whether it is on the curve.
        """
        if point.coordinate_model.curve_model != self.model:
            return False
        if self.is_neutral(point):
            return True
        if isinstance(point.coordinate_model, AffineCoordinateModel):
            loc = {**self.parameters, **point.coords}
        else:
            loc = {**self.parameters, **point.to_affine().coords}
        return eval(compile(self.model.equation, "", mode="eval"), loc)

    def to_affine(self) -> "EllipticCurve":
        """
        Convert this curve into the affine coordinate model, if possible.

        :return: The transformed elliptic curve.
        """
        coord_model = AffineCoordinateModel(self.model)
        return EllipticCurve(self.model, coord_model, self.prime, self.neutral.to_affine(), self.parameters)  # type: ignore[arg-type]

    def decode_point(self, encoded: bytes) -> Point:
        """
        Decode a point encoded as a sequence of bytes (ANSI X9.62). This decoding is the same as ANSI X9.63 for
        the affine coordinate system and for others it only implements the uncompressed variant.

        .. warning::
            The point is not validated to be on the curve (if the uncompressed encoding is used).

        :param encoded: The encoded representation of a point.
        :return: The decoded point.
        """
        if encoded[0] == 0x00 and len(encoded) == 1:
            return InfinityPoint(self.coordinate_model)
        coord_len = (self.prime.bit_length() + 7) // 8
        if encoded[0] in (0x04, 0x06):
            data = encoded[1:]
            if len(data) != coord_len * len(self.coordinate_model.variables):
                raise ValueError("Encoded point has bad length")
            coords = {}
            for var in sorted(self.coordinate_model.variables):
                coords[var] = Mod(int.from_bytes(data[:coord_len], "big"), self.prime)
                data = data[coord_len:]
            return Point(self.coordinate_model, **coords)
        elif encoded[0] in (0x02, 0x03):
            if isinstance(self.coordinate_model, AffineCoordinateModel):
                data = encoded[1:]
                if len(data) != coord_len:
                    raise ValueError("Encoded point has bad length")
                x = Mod(int.from_bytes(data, "big"), self.prime)
                loc = {**self.parameters, "x": x}
                rhs = eval(compile(self.model.ysquared, "", mode="eval"), loc)
                if not rhs.is_residue():
                    raise ValueError("Point not on curve")
                sqrt = rhs.sqrt()
                yp = encoded[0] & 0x01
                if int(sqrt) & 0x01 == yp:
                    y = sqrt
                else:
                    y = -sqrt
                return Point(self.coordinate_model, x=x, y=y)
            else:
                raise NotImplementedError
        else:
            raise ValueError(f"Wrong encoding type: {hex(encoded[0])}, should be one of 0x04, 0x06, 0x02, 0x03 or 0x00")

    def affine_random(self) -> Point:
        """Generate a random affine point on the curve."""
        while True:
            x = Mod.random(self.prime)
            loc = {**self.parameters, "x": x}
            ysquared = eval(compile(self.model.ysquared, "", mode="eval"), loc)
            if ysquared.is_residue():
                y = ysquared.sqrt()
                b = Mod.random(2)
                if b == 1:
                    y = -y
                return Point(AffineCoordinateModel(self.model), x=x, y=y)

    def __eq__(self, other):
        if not isinstance(other, EllipticCurve):
            return False
        return self.model == other.model and self.coordinate_model == other.coordinate_model and self.prime == other.prime and self.parameters == other.parameters

    def __str__(self):
        return "EllipticCurve"

    def __repr__(self):
        params = ", ".join((f"{key}={val}" for key, val in self.parameters.items()))
        return f"{self.__class__.__name__}([{params}] on {self.model} using {self.coordinate_model})"
