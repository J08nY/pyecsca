"""Provides functions for transforming curves to different models."""
from public import public
from sympy import FF, symbols, Poly

from .coordinates import AffineCoordinateModel
from .curve import EllipticCurve
from .mod import Mod
from .model import ShortWeierstrassModel, MontgomeryModel, TwistedEdwardsModel
from .params import DomainParameters
from .point import InfinityPoint, Point


def __M_map(params, param_names, map_parameters, map_point, model):
    param_one = params.curve.parameters[param_names[0]]
    param_other = params.curve.parameters[param_names[1]]
    parameters = map_parameters(param_one, param_other)
    aff = AffineCoordinateModel(model)
    if isinstance(params.curve.neutral, InfinityPoint):
        neutral = InfinityPoint(aff)
    else:
        neutral = map_point(param_one, param_other, params.curve.neutral, aff)
    curve = EllipticCurve(model, aff, params.curve.prime, neutral, parameters)
    return DomainParameters(
        curve,
        map_point(param_one, param_other, params.generator, aff),
        params.order,
        params.cofactor,
    )


@public
def M2SW(params: DomainParameters) -> DomainParameters:
    """
    Convert a Montgomery curve to ShortWeierstrass.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, MontgomeryModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError

    def map_parameters(A, B):
        a = (3 - A ** 2) / (3 * B ** 2)
        b = (2 * A ** 3 - 9 * A) / (27 * B ** 3)
        return {"a": a, "b": b}

    def map_point(A, B, pt, aff):
        u = pt.x / B + A / (3 * B)
        v = pt.y / B
        return Point(aff, x=u, y=v)

    return __M_map(
        params, ("a", "b"), map_parameters, map_point, ShortWeierstrassModel()
    )


@public
def M2TE(params: DomainParameters) -> DomainParameters:
    """
    Convert a Montgomery curve to TwistedEdwards.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, MontgomeryModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError

    def map_parameters(A, B):
        a = (A + 2) / B
        d = (A - 2) / B
        return {"a": a, "d": d}

    def map_point(A, B, pt, aff):
        u = pt.x / pt.y
        v = (pt.x - 1) / (pt.x + 1)
        return Point(aff, x=u, y=v)

    return __M_map(params, ("a", "b"), map_parameters, map_point, TwistedEdwardsModel())


@public
def TE2M(params: DomainParameters) -> DomainParameters:
    """
    Convert a TwistedEdwards curve to Montgomery.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, TwistedEdwardsModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError

    def map_parameters(a, d):
        A = (2 * (a + d)) / (a - d)
        B = 4 / (a - d)
        return {"a": A, "b": B}

    def map_point(a, d, pt, aff):
        u = (1 + pt.y) / (1 - pt.y)
        v = (1 + pt.y) / ((1 - pt.y) * pt.x)
        return Point(aff, x=u, y=v)

    return __M_map(params, ("a", "d"), map_parameters, map_point, MontgomeryModel())


@public
def SW2M(params: DomainParameters) -> DomainParameters:
    """
    Convert a ShortWeierstrass curve to Montgomery.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, ShortWeierstrassModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError
    ax = symbols("α")
    field = FF(params.curve.prime)
    rhs = Poly(
        ax ** 3
        + field(int(params.curve.parameters["a"])) * ax
        + field(int(params.curve.parameters["b"])),
        ax,
        domain=field,
    )
    roots = rhs.ground_roots()
    if not roots:
        raise ValueError(
            "Curve cannot be transformed to Montgomery model (x^3 + ax + b has no root)."
        )
    alpha = Mod(int(next(iter(roots.keys()))), params.curve.prime)
    beta = (3 * alpha ** 2 + params.curve.parameters["a"]).sqrt()

    def map_parameters(a, b):
        A = (3 * alpha) / beta
        B = 1 / beta
        return {"a": A, "b": B}

    def map_point(a, b, pt, aff):
        u = (pt.x - alpha) / beta
        v = pt.y / beta
        return Point(aff, x=u, y=v)

    return __M_map(params, ("a", "b"), map_parameters, map_point, MontgomeryModel())


@public
def SW2TE(params: DomainParameters) -> DomainParameters:
    """
    Convert a ShortWeierstrass curve to TwistedEdwards.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, ShortWeierstrassModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError
    ax = symbols("α")
    field = FF(params.curve.prime)
    rhs = Poly(
        ax ** 3
        + field(int(params.curve.parameters["a"])) * ax
        + field(int(params.curve.parameters["b"])),
        ax,
        domain=field,
    )
    roots = rhs.ground_roots()
    if not roots:
        raise ValueError(
            "Curve cannot be transformed to Montgomery model (x^3 + ax + b has no root)."
        )
    alpha = Mod(int(next(iter(roots.keys()))), params.curve.prime)
    beta = (3 * alpha ** 2 + params.curve.parameters["a"]).sqrt()

    def map_parameters(a, b):
        a = 3 * alpha + 2 * beta
        d = 3 * alpha - 2 * beta
        return {"a": a, "d": d}

    def map_point(a, b, pt, aff):
        if params.curve.is_neutral(pt):
            u = Mod(0, params.curve.prime)
            v = Mod(1, params.curve.prime)
        elif pt.x == alpha and pt.y == 0:
            u = Mod(0, params.curve.prime)
            v = Mod(-1, params.curve.prime)
        else:
            u = (pt.x - alpha) / pt.y
            v = (pt.x - alpha - beta) / (pt.x - alpha + beta)
        return Point(aff, x=u, y=v)

    return __M_map(params, ("a", "b"), map_parameters, map_point, TwistedEdwardsModel())
