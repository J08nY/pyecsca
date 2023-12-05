from typing import List, Callable, Any
from public import public

from . import Formula
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


@public
def expand_formula_list(
    formulas: List[EFDFormula], norm: Callable[[Formula], Any] = ivs_norm
) -> List[EFDFormula]:
    extended = reduce_with_similarity(formulas, norm)

    fliparood: List[EFDFormula] = sum(list(map(recursive_fliparoo, extended)), [])
    extended.extend(fliparood)
    extended = reduce_with_similarity(extended, norm)

    switch_signs: List[EFDFormula] = sum(
        [list(generate_switched_formulas(f)) for f in extended], []
    )
    extended.extend(switch_signs)
    extended = reduce_with_similarity(extended, norm)

    extended.extend(list(map(reduce_all_adds, extended)))
    extended = reduce_with_similarity(extended, norm)

    extended.extend(list(map(expand_all_muls, extended)))
    extended = reduce_with_similarity(extended, norm)

    extended.extend(list(map(expand_all_nopower2_muls, extended)))
    extended = reduce_with_similarity(extended, norm)

    return extended
