"""Provides metrics for comparing formulas."""

import warnings

from public import public
from typing import Dict
from operator import itemgetter, attrgetter

from pyecsca.ec.formula.unroll import unroll_formula
from pyecsca.ec.formula.base import Formula
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.context import DefaultContext, local


@public
def formula_ivs(formula: Formula):
    one_unroll = unroll_formula(formula)
    one_results = {}
    for name, value in one_unroll:
        if name in formula.outputs:
            one_results[name] = value
    one_polys = set(map(itemgetter(1), one_unroll))
    return one_polys, set(one_results.values())


@public
def ivs_norm(one: Formula):
    return formula_ivs(one)[0]


@public
def formula_similarity(one: Formula, other: Formula) -> Dict[str, float]:
    """
    Formula similarity based on symbolic intermediate value sets.

    :param one:
    :param other:
    :return:
    """
    if one.coordinate_model != other.coordinate_model:
        warnings.warn("Mismatched coordinate model.")

    one_polys, one_result_polys = formula_ivs(one)
    other_polys, other_result_polys = formula_ivs(other)
    return {
        "output": len(one_result_polys.intersection(other_result_polys))
        / max(len(one_result_polys), len(other_result_polys)),
        "ivs": len(one_polys.intersection(other_polys))
        / max(len(one_polys), len(other_polys)),
    }


@public
def formula_similarity_abs(one: Formula, other: Formula) -> Dict[str, float]:
    """
    Formula similarity based on symbolic intermediate value sets (absolute value)

    :param one:
    :param other:
    :return:
    """
    if one.coordinate_model != other.coordinate_model:
        warnings.warn("Mismatched coordinate model.")

    one_polys, one_result_polys = formula_ivs(one)
    other_polys, other_result_polys = formula_ivs(other)

    one_polys = {f if f.LC() > 0 else -f for f in one_polys}
    other_polys = {f if f.LC() > 0 else -f for f in other_polys}

    one_result_polys = {f if f.LC() > 0 else -f for f in one_result_polys}
    other_result_polys = {f if f.LC() > 0 else -f for f in other_result_polys}
    return {
        "output": len(one_result_polys.intersection(other_result_polys))
        / max(len(one_result_polys), len(other_result_polys)),
        "ivs": len(one_polys.intersection(other_polys))
        / max(len(one_polys), len(other_polys)),
    }


@public
def formula_similarity_fuzz(
    one: Formula, other: Formula, curve: EllipticCurve, samples: int = 1000
) -> Dict[str, float]:
    """
    Formula similarity based on random computation.

    :param one:
    :param other:
    :return:
    """
    if one.coordinate_model != other.coordinate_model:
        raise ValueError("Mismatched coordinate model.")

    output_matches = 0.0
    iv_matches = 0.0
    for _ in range(samples):
        Paff = curve.affine_random()
        Qaff = curve.affine_random()
        Raff = curve.affine_add(Paff, Qaff)
        P = Paff.to_model(one.coordinate_model, curve)
        Q = Qaff.to_model(one.coordinate_model, curve)
        R = Raff.to_model(one.coordinate_model, curve)
        inputs = (P, Q, R)[: one.num_inputs]
        with local(DefaultContext()) as ctx:
            res_one = one(curve.prime, *inputs, **curve.parameters)
        action_one = ctx.actions[0].action
        ivs_one = set(
            map(attrgetter("value"), sum(action_one.intermediates.values(), []))
        )
        with local(DefaultContext()) as ctx:
            res_other = other(curve.prime, *inputs, **curve.parameters)
        action_other = ctx.actions[0].action
        ivs_other = set(
            map(attrgetter("value"), sum(action_other.intermediates.values(), []))
        )
        iv_matches += len(ivs_one.intersection(ivs_other)) / max(
            len(ivs_one), len(ivs_other)
        )
        one_coords = set(res_one)
        other_coords = set(res_other)
        output_matches += len(one_coords.intersection(other_coords)) / max(
            len(one_coords), len(other_coords)
        )
    return {"output": output_matches / samples, "ivs": iv_matches / samples}
