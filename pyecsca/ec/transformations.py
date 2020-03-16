from public import public

from .coordinates import AffineCoordinateModel
from .curve import EllipticCurve
from .model import ShortWeierstrassModel, MontgomeryModel, TwistedEdwardsModel
from .params import DomainParameters
from .point import InfinityPoint, Point


def __M_map(params, map_parameters, map_point, model):
    A = params.curve.parameters["a"]
    B = params.curve.parameters["b"]
    parameters = map_parameters(A, B)
    aff = AffineCoordinateModel(model)
    if isinstance(params.curve.neutral, InfinityPoint):
        neutral = InfinityPoint(aff)
    else:
        neutral = map_point(A, B, params.curve.neutral, aff)
    curve = EllipticCurve(model, aff, params.curve.prime, neutral, parameters)
    return DomainParameters(curve, map_point(A, B, params.generator, aff), params.order,
                            params.cofactor)


@public
def M2SW(params: DomainParameters) -> DomainParameters:
    """
    Convert a Montgomery curve to ShortWeierstrass.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, MontgomeryModel) or not isinstance(
            params.curve.coordinate_model, AffineCoordinateModel):
        raise ValueError

    def map_parameters(A, B):
        a = (3 - A ** 2) / (3 * B ** 2)
        b = (2 * A ** 3 - 9 * A) / (27 * B ** 3)
        return {"a": a, "b": b}

    def map_point(A, B, pt, aff):
        u = pt.x / B + A / (3 * B)
        v = pt.y / B
        return Point(aff, x=u, y=v)

    return __M_map(params, map_parameters, map_point, ShortWeierstrassModel())


@public
def M2TE(params: DomainParameters) -> DomainParameters:
    """
    Convert a Montgomery curve to TwistedEdwards.

    :param params: The domain parameters to convert.
    :return: The converted domain parameters.
    """
    if not isinstance(params.curve.model, MontgomeryModel) or not isinstance(
            params.curve.coordinate_model, AffineCoordinateModel):
        raise ValueError

    def map_parameters(A, B):
        a = (A + 2) / B
        d = (A - 2) / B
        return {"a": a, "d": d}

    def map_point(A, B, pt, aff):
        u = pt.x / pt.y
        v = (pt.x - 1) / (pt.x + 1)
        return Point(aff, x=u, y=v)

    return __M_map(params, map_parameters, map_point, TwistedEdwardsModel())
