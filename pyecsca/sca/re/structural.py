""""""
from typing import Dict
from public import public

from ...ec.curve import EllipticCurve
from ...ec.formula import Formula
from ...ec.context import DefaultContext, local
from .zvp import unroll_formula
from operator import itemgetter, attrgetter


@public
def formula_similarity(one: Formula, other: Formula) -> Dict[str, float]:
    if one.coordinate_model != other.coordinate_model:
        raise ValueError("Mismatched coordinate model.")

    one_unroll = unroll_formula(one)
    other_unroll = unroll_formula(other)
    one_results = {}
    for name, value in one_unroll:
        if name in one.outputs:
            one_results[name] = value
    other_results = {}
    for name, value in other_unroll:
        if name in other.outputs:
            other_results[name] = value
    one_result_polys = set(one_results.values())
    other_result_polys = set(other_results.values())
    one_polys = set(map(itemgetter(1), one_unroll))
    other_polys = set(map(itemgetter(1), other_unroll))
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
        action_one = ctx.actions.get_by_index([0])
        ivs_one = set(
            map(attrgetter("value"), sum(action_one[0].intermediates.values(), []))
        )
        with local(DefaultContext()) as ctx:
            res_other = other(curve.prime, *inputs, **curve.parameters)
        action_other = ctx.actions.get_by_index([0])
        ivs_other = set(
            map(attrgetter("value"), sum(action_other[0].intermediates.values(), []))
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
