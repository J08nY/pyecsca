"""Provides a formula expansion function."""
from typing import Set, Callable, Any
from public import public

from pyecsca.ec.formula.base import Formula
from pyecsca.ec.formula.efd import EFDFormula
from pyecsca.ec.formula.fliparoo import recursive_fliparoo
from pyecsca.ec.formula.metrics import ivs_norm
from pyecsca.ec.formula.partitions import reduce_all_adds, expand_all_muls, expand_all_nopower2_muls
from pyecsca.ec.formula.switch_sign import generate_switched_formulas


def reduce_with_similarity(
    formulas: Set[Formula], norm: Callable[[Formula], Any]
) -> Set[Formula]:
    reduced = set(filter(lambda x: isinstance(x, EFDFormula), formulas))
    similarities = list(map(norm, reduced))
    for formula in formulas:
        n = norm(formula)
        if n in similarities:
            continue
        similarities.append(n)
        reduced.add(formula)
    return reduced


@public
def expand_formula_set(
    formulas: Set[Formula], norm: Callable[[Formula], Any] = ivs_norm
) -> Set[Formula]:
    """
    Expand a set of formulas by using transformations:
     - Fliparoos
     - Sign switching
     - Associativity and Commutativity

    :param formulas:
    :param norm:
    :return:
    """
    extended = reduce_with_similarity(formulas, norm)

    fliparood: Set[Formula] = set().union(*map(recursive_fliparoo, extended))
    extended.update(fliparood)
    extended = reduce_with_similarity(extended, norm)

    switch_signs: Set[Formula] = set().union(
        *(set(generate_switched_formulas(f)) for f in extended)
    )
    extended.update(switch_signs)
    extended = reduce_with_similarity(extended, norm)

    extended.update(set(map(reduce_all_adds, extended)))
    extended = reduce_with_similarity(extended, norm)

    extended.update(set(map(expand_all_muls, extended)))
    extended = reduce_with_similarity(extended, norm)

    extended.update(set(map(expand_all_nopower2_muls, extended)))
    extended = reduce_with_similarity(extended, norm)

    return extended
