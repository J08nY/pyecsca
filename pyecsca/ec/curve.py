"""Provides an elliptic curve class."""
from ast import Module
from astunparse import unparse
from copy import copy
from typing import MutableMapping, Union, List, Optional, Dict, Set

from public import public
from sympy import FF

from pyecsca.misc.cache import sympify
from pyecsca.misc.cfg import getconfig

from pyecsca.ec.coordinates import CoordinateModel, AffineCoordinateModel
from pyecsca.ec.error import raise_unsatisified_assumption
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.model import CurveModel
from pyecsca.ec.point import Point, InfinityPoint


@public
class EllipticCurve:
    """
    An elliptic curve.

    >>> from pyecsca.ec.params import get_params
    >>> params = get_params("secg", "secp256r1", "projective")
    >>> curve = params.curve
    >>> curve.prime
    115792089210356248762697446949407573530086143415290314195533631308867097853951
    >>> curve.parameters  # doctest: +NORMALIZE_WHITESPACE
    {'a': 115792089210356248762697446949407573530086143415290314195533631308867097853948,
     'b': 41058363725152142129326129780047268409114441015993725554835256314039467401291}
    >>> curve.neutral
    InfinityPoint(shortw/projective)

    You can also use the curve object to operate on affine points.

    >>> from pyecsca.ec.coordinates import AffineCoordinateModel
    >>> affine = AffineCoordinateModel(curve.model)
    >>> points_P = sorted(curve.affine_lift_x(mod(5, curve.prime)), key=lambda p: int(p.y))
    >>> points_P  # doctest: +NORMALIZE_WHITESPACE
    [Point([x=5, y=31468013646237722594854082025316614106172411895747863909393730389177298123724] in shortw/affine),
     Point([x=5, y=84324075564118526167843364924090959423913731519542450286139900919689799730227] in shortw/affine)]
    >>> P = points_P[0]
    >>> Q = Point(affine, x=mod(106156966968002564385990772707119429362097710917623193504777452220576981858057, curve.prime), y=mod(89283496902772247016522581906930535517715184283144143693965440110672128480043, curve.prime))
    >>> curve.affine_add(P, Q)
    Point([x=110884201872336783252492544257507655322265785208411447156687491781308462893723, y=17851997459724035659875545393642578516937407971293368958749928013979790074156] in shortw/affine)
    >>> curve.affine_multiply(P, 10)
    Point([x=102258728610797412855984739741975475478412665729440354248608608794190482472287, y=6863906685124263315402674958985193889511160759072519051123564041627571792194] in shortw/affine)
    >>> curve.affine_random()  # doctest: +ELLIPSIS
    Point([x=..., y=...] in shortw/affine)
    >>> curve.is_on_curve(P)
    True
    >>> curve.is_neutral(P)
    False

    """

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

    def __init__(
            self,
            model: CurveModel,
            coordinate_model: CoordinateModel,
            prime: int,
            neutral: Point,
            parameters: MutableMapping[str, Union[Mod, int]],
    ):
        if coordinate_model not in model.coordinates.values() and not isinstance(
                coordinate_model, AffineCoordinateModel
        ):
            raise ValueError
        if (
                set(model.parameter_names)
                .union(coordinate_model.parameters)
                .symmetric_difference(parameters.keys())
        ):
            raise ValueError
        self.model = model
        self.coordinate_model = coordinate_model
        self.prime = prime
        self.parameters = {}
        for name, value in parameters.items():
            if isinstance(value, Mod):
                if value.n != prime:
                    raise ValueError(f"Parameter {name} has wrong modulus.")
                val = value
            else:
                val = mod(value, prime)
            self.parameters[name] = val
        self.neutral = neutral
        self.__validate_coord_assumptions()

    def __validate_coord_assumptions(self):
        for assumption in self.coordinate_model.assumptions:
            # Try to execute assumption, if it works, check with curve parameters
            # if it doesn't work, move all over to rhs and construct a sympy polynomial of it
            # then find roots and take first one for new value for new coordinate parameter.
            try:
                alocals: Dict[str, Union[Mod, int]] = {}
                compiled = compile(assumption, "", mode="exec")
                exec(compiled, None, alocals)  # exec is OK here, skipcq: PYL-W0122
                for param, value in alocals.items():
                    if self.parameters[param] != value:
                        raise_unsatisified_assumption(
                            getconfig().ec.unsatisfied_coordinate_assumption_action,
                            f"Coordinate model {self.coordinate_model} has an unsatisifed assumption on the {param} parameter (= {value}).",
                        )
            except NameError:
                k = FF(self.prime)
                assumption_string = unparse(assumption).strip()
                lhs, rhs = assumption_string.split(" = ")
                expr = sympify(f"{rhs} - {lhs}")
                for symbol in expr.free_symbols:
                    if (val := self.parameters.get(str(symbol), None)) is not None:
                        expr = expr.xreplace({symbol: val})
                if len(expr.free_symbols) > 0:
                    raise ValueError(
                        f"Missing necessary coordinate model parameter ({assumption_string})."
                    )
                if k.from_sympy(expr) != 0:
                    raise_unsatisified_assumption(
                        getconfig().ec.unsatisfied_coordinate_assumption_action,
                        f"Coordinate model {self.coordinate_model} has an unsatisifed assumption on the {param} parameter (0 = {expr})."
                    )

    def _execute_base_formulas(self, formulas: List[Module], *points: Point) -> Point:
        for point in points:
            if not isinstance(point.coordinate_model, AffineCoordinateModel):
                raise ValueError("Coordinate model of point is not affine.")
            if point.coordinate_model.curve_model != self.model:
                raise ValueError("Curve model of point does not match the curve.")
        locls = {
            var + str(i + 1): point.coords[var]
            for i, point in enumerate(points)
            for var in point.coords
        }
        locls.update(self.parameters)
        for line in formulas:
            exec(compile(line, "", mode="exec"), None, locls)  # exec is OK here, skipcq: PYL-W0122
        if not isinstance(locls["x"], Mod):
            locls["x"] = mod(locls["x"], self.prime)
        if not isinstance(locls["y"], Mod):
            locls["y"] = mod(locls["y"], self.prime)
        return Point(AffineCoordinateModel(self.model), x=locls["x"], y=locls["y"])

    def affine_add(self, one: Point, other: Point) -> Point:
        """
        Add two affine points using the affine addition formula.

        Handles the case of point at infinity gracefully (short-circuits).

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

        Handles the case of point at infinity gracefully (short-circuits).

        :param one: A point.
        :return: The doubling of the point.
        """
        if isinstance(one, InfinityPoint):
            return one
        return self._execute_base_formulas(self.model.base_doubling, one)

    def affine_negate(self, one: Point) -> Point:
        """
        Negate an affine point using the affine negation formula.

        Handles the case of point at infinity gracefully (short-circuits).

        :param one: A point.
        :return: The negation of the point.
        """
        if isinstance(one, InfinityPoint):
            return one
        return self._execute_base_formulas(self.model.base_negation, one)

    def affine_multiply(self, point: Point, scalar: int) -> Point:
        """
        Multiply an affine point by a scalar using the affine doubling and addition formulas.

        Handles the case of point at infinity gracefully (short-circuits).

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
        Get the neutral point in affine form, if it has one, otherwise ``None``.

        :return: The affine neutral point or ``None``.
        """
        if not self.neutral_is_affine:
            return None
        locls = {**self.parameters}
        for line in self.model.base_neutral:
            exec(compile(line, "", mode="exec"), None, locls)  # exec is OK here, skipcq: PYL-W0122
        if not isinstance(locls["x"], Mod):
            locls["x"] = mod(locls["x"], self.prime)
        if not isinstance(locls["y"], Mod):
            locls["y"] = mod(locls["y"], self.prime)
        return Point(AffineCoordinateModel(self.model), x=locls["x"], y=locls["y"])

    @property
    def neutral_is_affine(self):
        """Whether the neutral point is an affine point."""
        return bool(self.model.base_neutral)

    def is_neutral(self, point: Point) -> bool:
        """
        Check whether the point is the neutral point.

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
        return eval(compile(self.model.equation, "", mode="eval"), loc)  # eval is OK here, skipcq: PYL-W0123

    def to_coords(self, coordinate_model: CoordinateModel) -> "EllipticCurve":
        """
        Convert this curve into a different coordinate model, only possible if it is currently affine.

        :param coordinate_model: The target coordinate model.
        :return: The transformed elliptic curve.
        """
        if not isinstance(self.coordinate_model, AffineCoordinateModel):
            raise ValueError
        return EllipticCurve(self.model, coordinate_model, self.prime, self.neutral.to_model(coordinate_model, self),
                             self.parameters)  # type: ignore[arg-type]

    def to_affine(self) -> "EllipticCurve":
        """
        Convert this curve into the affine coordinate model, if possible.

        :return: The transformed elliptic curve.
        """
        coord_model = AffineCoordinateModel(self.model)
        return EllipticCurve(self.model, coord_model, self.prime, self.neutral.to_affine(),
                             self.parameters)  # type: ignore[arg-type]

    def decode_point(self, encoded: bytes) -> Point:
        """
        Decode a point encoded as a sequence of bytes (ANSI X9.62).

        This decoding is the same as ANSI X9.63 for the affine coordinate system and for others it
        only implements the uncompressed variant.

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
                coords[var] = mod(int.from_bytes(data[:coord_len], "big"), self.prime)
                data = data[coord_len:]
            return Point(self.coordinate_model, **coords)
        elif encoded[0] in (0x02, 0x03):
            if isinstance(self.coordinate_model, AffineCoordinateModel):
                data = encoded[1:]
                if len(data) != coord_len:
                    raise ValueError("Encoded point has bad length")
                x = mod(int.from_bytes(data, "big"), self.prime)
                loc = {**self.parameters, "x": x}
                rhs = eval(compile(self.model.ysquared, "", mode="eval"), loc)  # eval is OK here, skipcq: PYL-W0123
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
            raise ValueError(
                f"Wrong encoding type: {hex(encoded[0])}, should be one of 0x04, 0x06, 0x02, 0x03 or 0x00"
            )

    def affine_lift_x(self, x: Mod) -> Set[Point]:
        """
        Lift an x-coordinate to the curve.

        :param x: The x-coordinate.
        :return: Lifted (affine) points, if any.
        """
        loc = {**self.parameters, "x": x}
        ysquared = eval(compile(self.model.ysquared, "", mode="eval"), loc)  # eval is OK here, skipcq: PYL-W0123
        if not ysquared.is_residue():
            return set()
        y = ysquared.sqrt()
        return {Point(AffineCoordinateModel(self.model), x=x, y=y),
                Point(AffineCoordinateModel(self.model), x=x, y=-y)}

    def affine_random(self) -> Point:
        """Generate a random affine point on the curve."""
        while True:
            x = Mod.random(self.prime)
            loc = {**self.parameters, "x": x}
            ysquared = eval(compile(self.model.ysquared, "", mode="eval"), loc)  # eval is OK here, skipcq: PYL-W0123
            if ysquared.is_residue():
                y = ysquared.sqrt()
                b = Mod.random(2)
                if b == 1:
                    y = -y
                return Point(AffineCoordinateModel(self.model), x=x, y=y)

    def __eq__(self, other):
        if not isinstance(other, EllipticCurve):
            return False
        return (
                self.model == other.model
                and self.coordinate_model == other.coordinate_model
                and self.prime == other.prime
                and self.parameters == other.parameters
        )

    def __hash__(self):
        return hash((self.model, self.coordinate_model, self.prime, tuple(self.parameters.keys()), tuple(self.parameters.values())))

    def __str__(self):
        return "EllipticCurve"

    def __repr__(self):
        params = ", ".join((f"{key}={val}" for key, val in self.parameters.items()))
        return f"{self.__class__.__name__}([{params}] p={self.prime} on {self.coordinate_model})"
