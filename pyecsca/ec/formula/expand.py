from typing import List

from .efd import EFDFormula
from .fliparoo import recursive_fliparoo
from .graph import ModifiedEFDFormula
from .metrics import ivs_norm
from .partitions import reduce_all_adds, expand_all_muls, expand_all_nopower2_muls
from .switch_sign import generate_switched_formulas


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


def expand_formula_list(formulas: List[EFDFormula]):
    extended_efd = reduce_with_similarity(formulas, ivs_norm)
    print(f"Reduced to {len(extended_efd)} formulas")

    fliparood: List[EFDFormula] = sum(list(map(recursive_fliparoo, extended_efd)), [])
    extended_efd.extend(fliparood)
    print(f"Fliparoo: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, ivs_norm)
    print(f"Reduced to {len(extended_efd)} formulas")
    # list(map(test_formula, extended_efd))

    switch_signs: List[EFDFormula] = sum([list(generate_switched_formulas(f)) for f in extended_efd], [])
    extended_efd.extend(switch_signs)
    print(f"Switch signs: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, ivs_norm)
    print(f"Reduced to {len(extended_efd)} formulas")
    # list(map(test_formula, extended_efd))

    extended_efd.extend(list(map(reduce_all_adds, extended_efd)))
    print(f"Compress adds: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, ivs_norm)
    print(f"Reduced to {len(extended_efd)} formulas")
    # list(map(test_formula, extended_efd))

    extended_efd.extend(list(map(expand_all_muls, extended_efd)))
    print(f"Expand muls: {len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, ivs_norm)
    print(f"Reduced to {len(extended_efd)} formulas")
    # list(map(test_formula, extended_efd))

    extended_efd.extend(list(map(expand_all_nopower2_muls, extended_efd)))
    print(f"Expand muls(!=2^):{len(extended_efd)} formulas")
    extended_efd = reduce_with_similarity(extended_efd, ivs_norm)
    print(f"Reduced to {len(extended_efd)} formulas")
    # list(map(test_formula, extended_efd))
