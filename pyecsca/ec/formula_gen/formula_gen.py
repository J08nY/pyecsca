from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel, TwistedEdwardsModel
from pyecsca.ec.formula_gen.test import load_efd_formulas, load_library_formulas
from pyecsca.ec.formula_gen.formula_graph import ModifiedEFDFormula
from pyecsca.ec.formula_gen.fliparoo import generate_fliparood_formulas
from pyecsca.ec.formula_gen.switch_sign import generate_switched_formulas
from pyecsca.ec.formula_gen.partitions import (
    reduce_all_adds,
    expand_all_muls,
    expand_all_nopower2_muls,
)
from pyecsca.ec.formula import EFDFormula, Formula
from typing import List, Dict
from operator import itemgetter
from tqdm.notebook import tqdm
from pyecsca.sca.re.zvp import unroll_formula
import warnings
from pyecsca.ec.formula_gen.test import test_formula


def main():
    efd = load_efd_formulas("projective", ShortWeierstrassModel())

    extended_efd = list(efd.values())
    print(f"{len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, iv_set)
    print(f"Reduced to {len(extended_efd)} formulas")

    fliparood = sum(list(map(recursive_fliparoo, extended_efd)), [])
    extended_efd.extend(fliparood)
    print(f"Fliparoo: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, iv_set)
    print(f"Reduced to {len(extended_efd)} formulas")
    list(map(test_formula, extended_efd))

    switch_signs = sum([list(generate_switched_formulas(f)) for f in extended_efd], [])
    extended_efd.extend(switch_signs)
    print(f"Switch signs: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, iv_set)
    print(f"Reduced to {len(extended_efd)} formulas")
    list(map(test_formula, extended_efd))

    extended_efd.extend(list(map(reduce_all_adds, extended_efd)))
    print(f"Compress adds: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, iv_set)
    print(f"Reduced to {len(extended_efd)} formulas")
    list(map(test_formula, extended_efd))

    extended_efd.extend(list(map(expand_all_muls, extended_efd)))
    print(f"Expand muls: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, iv_set)
    print(f"Reduced to {len(extended_efd)} formulas")
    list(map(test_formula, extended_efd))

    extended_efd.extend(list(map(expand_all_nopower2_muls, extended_efd)))
    print(f"Expand muls(!=2^):{len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, iv_set)
    print(f"Reduced to {len(extended_efd)} formulas")
    list(map(test_formula, extended_efd))

    return extended_efd


def reduce_with_similarity(formulas: List[EFDFormula], norm):
    efd = list(filter(lambda x: not isinstance(x, ModifiedEFDFormula), formulas))
    reduced_efd = efd
    similarities = list(map(norm, efd))
    for formula in formulas:
        n = norm(formula)
        if n in similarities:
            continue
        similarities.append(n)
        reduced_efd.append(formula)
    return reduced_efd


def formula_similarity(one: Formula, other: Formula) -> Dict[str, float]:
    if one.coordinate_model != other.coordinate_model:
        warnings.warn("Mismatched coordinate model.")

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


def iv_set(one: Formula):
    one_unroll = unroll_formula(one)
    one_results = {}
    for name, value in one_unroll:
        if name in one.outputs:
            one_results[name] = value
    one_polys = set(map(itemgetter(1), one_unroll))
    return one_polys


def recursive_fliparoo(formula, depth=2):
    all_fliparoos = {0: [formula]}
    counter = 0
    while depth > counter:
        prev_level = all_fliparoos[counter]
        fliparoo_level = []
        for flipparood_formula in prev_level:
            rename = not counter  # rename ivs before the first fliparoo
            for newly_fliparood in generate_fliparood_formulas(
                flipparood_formula, rename
            ):
                fliparoo_level.append(newly_fliparood)
        counter += 1
        all_fliparoos[counter] = fliparoo_level

    return sum(all_fliparoos.values(), [])


if __name__ == "__main__":
    main()
