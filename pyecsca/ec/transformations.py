"""Provides functions for transforming curves to different models."""
from typing import Tuple, Generator

from public import public
from sympy import FF, symbols, Poly

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.model import (
    ShortWeierstrassModel,
    MontgomeryModel,
    TwistedEdwardsModel,
    EdwardsModel,
)
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import InfinityPoint, Point


def __map(params, param_names, map_parameters, map_point, model):
    param_one = params.curve.parameters[param_names[0]]
    param_other = params.curve.parameters[param_names[1]]
    parameters = map_parameters(param_one, param_other)
    aff = AffineCoordinateModel(model)
    if isinstance(params.curve.neutral, InfinityPoint):
        neutral = InfinityPoint(aff)
    else:
        neutral = map_point(param_one, param_other, params.curve.neutral, aff)
    generator = map_point(param_one, param_other, params.generator, aff)
    curve = EllipticCurve(model, aff, params.curve.prime, neutral, parameters)
    return DomainParameters(
        curve,
        generator,
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
        a = (3 - A**2) / (3 * B**2)
        b = (2 * A**3 - 9 * A) / (27 * B**3)
        return {"a": a, "b": b}

    def map_point(A, B, pt, aff):
        u = pt.x / B + A / (3 * B)
        v = pt.y / B
        return Point(aff, x=u, y=v)

    return __map(params, ("a", "b"), map_parameters, map_point, ShortWeierstrassModel())


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

    return __map(params, ("a", "b"), map_parameters, map_point, TwistedEdwardsModel())


@public
def M2E(params: DomainParameters) -> DomainParameters:
    """
    Convert a Montgomery curve to Edwards.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, MontgomeryModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError

    def map_parameters(A, B):
        c = (B / (A + 2)).sqrt()
        d = (A**2 - 4) / (B**2)
        return {"c": c, "d": d}

    def map_point(A, B, pt, aff):
        u = pt.x / pt.y
        v = ((pt.x - 1) / (pt.x + 1)) * (B / (A + 2)).sqrt()
        return Point(aff, x=u, y=v)

    return __map(params, ("a", "b"), map_parameters, map_point, EdwardsModel())


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

    return __map(params, ("a", "d"), map_parameters, map_point, MontgomeryModel())


@public
def TE2E(params: DomainParameters) -> DomainParameters:
    """
    Convert a TwistedEdwards curve to Edwards.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, TwistedEdwardsModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError

    def map_parameters(a, d):
        c = a.sqrt().inverse()
        d = a * d
        return {"c": c, "d": d}

    def map_point(a, d, pt, aff):
        u = pt.x
        v = pt.y / a.sqrt().inverse()
        return Point(aff, x=u, y=v)

    return __map(params, ("a", "d"), map_parameters, map_point, EdwardsModel())


@public
def TE2SW(params: DomainParameters) -> DomainParameters:
    """
    Convert a TwistedEdwards curve to ShortWeierstrass.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, TwistedEdwardsModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError

    def map_parameters(A, D):
        a = -(A**2 + 14 * D * A + D**2) / 48
        b = (A + D) * (-(A**2) + 34 * A * D - D**2) / 864
        return {"a": a, "b": b}

    def map_point(A, D, pt, aff):
        u = (5 * A + A * pt.y - 5 * D * pt.y - D) / (12 - 12 * pt.y)
        v = (A + A * pt.y - D * pt.y - D) / (4 * pt.x - 4 * pt.x * pt.y)
        return Point(aff, x=u, y=v)

    return __map(params, ("a", "d"), map_parameters, map_point, ShortWeierstrassModel())


def __sw_ab(params: DomainParameters) -> Generator[Tuple[Mod, Mod], None, None]:
    if not isinstance(params.curve.model, ShortWeierstrassModel) or not isinstance(
        params.curve.coordinate_model, AffineCoordinateModel
    ):
        raise ValueError
    ax = symbols("α")
    field = FF(params.curve.prime)
    rhs = Poly(
        ax**3
        + field(int(params.curve.parameters["a"])) * ax
        + field(int(params.curve.parameters["b"])),
        ax,
        domain=field,
    )
    roots = rhs.ground_roots()
    if not roots:
        raise ValueError("Curve cannot be transformed (x^3 + ax + b has no root).")
    for root in roots:
        alpha = mod(int(root), params.curve.prime)
        beta = (3 * alpha**2 + params.curve.parameters["a"]).sqrt()
        yield alpha, beta


@public
def SW2M(params: DomainParameters) -> DomainParameters:
    """
    Convert a ShortWeierstrass curve to Montgomery.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    alpha, beta = next(iter(__sw_ab(params)))

    def map_parameters(a, b):
        A = (3 * alpha) / beta
        B = 1 / beta
        return {"a": A, "b": B}

    def map_point(a, b, pt, aff):
        u = (pt.x - alpha) / beta
        v = pt.y / beta
        return Point(aff, x=u, y=v)

    return __map(params, ("a", "b"), map_parameters, map_point, MontgomeryModel())


@public
def SW2TE(params: DomainParameters) -> DomainParameters:
    """
    Convert a ShortWeierstrass curve to TwistedEdwards.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    alpha, beta = next(iter(__sw_ab(params)))

    def map_parameters(a, b):
        a = 3 * alpha + 2 * beta
        d = 3 * alpha - 2 * beta
        return {"a": a, "d": d}

    def map_point(a, b, pt, aff):
        if params.curve.is_neutral(pt):
            u = mod(0, params.curve.prime)
            v = mod(1, params.curve.prime)
        elif pt.x == alpha and pt.y == 0:
            u = mod(0, params.curve.prime)
            v = mod(-1, params.curve.prime)
        else:
            u = (pt.x - alpha) / pt.y
            v = (pt.x - alpha - beta) / (pt.x - alpha + beta)
        return Point(aff, x=u, y=v)

    return __map(params, ("a", "b"), map_parameters, map_point, TwistedEdwardsModel())


@public
def SW2E(params: DomainParameters) -> DomainParameters:
    """
    Convert a ShortWeierstrass curve to Edwards.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    for alpha, beta in __sw_ab(params):
        s = beta.inverse()
        t = s / (3 * s * alpha + 2)
        if not t.is_residue():
            continue
        t = t.sqrt()

        def map_parameters(a, b):
            c = t
            d = -4 * a - 3 * alpha**2
            return {"c": c, "d": d}

        def map_point(a, b, pt, aff):
            u = (pt.x - alpha) / pt.y
            v = (s * (pt.x - alpha) - 1) / (s * (pt.x - alpha) + 1) * t
            return Point(aff, x=u, y=v)

        return __map(params, ("a", "b"), map_parameters, map_point, EdwardsModel())
    raise ValueError("Cannot convert.")
