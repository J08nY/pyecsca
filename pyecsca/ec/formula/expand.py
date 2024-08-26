"""Provides a formula expansion function."""

from typing import Set, Callable, Any, List, Iterable, Optional
from public import public
from operator import attrgetter
from functools import lru_cache

from pyecsca.ec.formula.base import Formula
from pyecsca.ec.formula.efd import EFDFormula
from pyecsca.ec.formula.fliparoo import recursive_fliparoo
from pyecsca.ec.formula.metrics import ivs_norm
from pyecsca.ec.formula.partitions import (
    reduce_all_adds,
    expand_all_muls,
    expand_all_nopower2_muls,
)
from pyecsca.ec.formula.switch_sign import generate_switched_formulas, switch_signs
from pyecsca.misc.utils import TaskExecutor


def reduce_with_similarity(
    formulas: List[Formula], norm: Callable[[Formula], Any]
) -> List[Formula]:
    formulas = reduce_by_eq(formulas)
    reduced = list(filter(lambda x: isinstance(x, EFDFormula), formulas))
    similarities = list(map(norm, reduced))
    for formula in formulas:
        n = norm(formula)
        if n in similarities:
            continue
        similarities.append(n)
        reduced.append(formula)
    return reduced


def reduce_by_eq(formulas: Iterable[Formula]) -> List[Formula]:
    unique = set()
    result = []
    for formula in formulas:
        if formula not in unique:
            unique.add(formula)
            result.append(formula)
    return result


@public
def expand_formula_set(
    formulas: Set[Formula], norm: Callable[[Formula], Any] = ivs_norm
) -> Set[Formula]:
    """
    Expand a set of formulas by using transformations:
     - Fliparoos
     - Sign switching
     - Associativity and Commutativity

    :param formulas: The set of formulas to expand.
    :param norm: The norm to use while reducing.
    :return: The expanded set of formulas.
    """

    @lru_cache(maxsize=1000)
    def cached(formula):
        return norm(formula)

    extended = sorted(formulas, key=attrgetter("name"))
    extended = reduce_with_similarity(extended, cached)

    fliparood: List[Formula] = reduce_by_eq(
        sum(map(lambda f: reduce_by_eq(recursive_fliparoo(f)), extended), [])
    )
    extended.extend(fliparood)
    extended = reduce_with_similarity(extended, cached)

    switch_signs: List[Formula] = reduce_by_eq(
        sum(map(lambda f: reduce_by_eq(generate_switched_formulas(f)), extended), [])
    )
    extended.extend(switch_signs)
    extended = reduce_with_similarity(extended, cached)

    add_reduced: List[Formula] = reduce_by_eq(list(map(reduce_all_adds, extended)))
    extended.extend(add_reduced)
    extended = reduce_with_similarity(extended, cached)

    mul_expanded: List[Formula] = reduce_by_eq(list(map(expand_all_muls, extended)))
    extended.extend(mul_expanded)
    extended = reduce_with_similarity(extended, cached)

    np2_expanded: List[Formula] = reduce_by_eq(
        list(map(expand_all_nopower2_muls, extended))
    )
    extended.extend(np2_expanded)
    extended = reduce_with_similarity(extended, cached)

    return set(reduce_by_eq(extended))


@public
def expand_formula_set_parallel(
    formulas: Set[Formula],
    norm: Callable[[Formula], Any] = ivs_norm,
    num_workers: int = 1,
) -> Set[Formula]:
    """
    Expand a set of formulas by using transformations (parallelized):
     - Fliparoos
     - Sign switching
     - Associativity and Commutativity

    :param formulas: The set of formulas to expand.
    :param norm: The norm to use while reducing.
    :param num_workers: The amount of workers to use.
    :return: The expanded set of formulas.
    """

    @lru_cache(maxsize=1000)
    def cached(formula):
        return norm(formula)

    def map_multiple(pool, formulas, fn):
        results: List[List[Formula]] = []
        for f in formulas:
            pool.submit_task(f, fn, f)
            results.append([])
        for f, future in pool.as_completed():
            results[formulas.index(f)] = reduce_by_eq(future.result())
        return reduce_by_eq(sum(results, []))

    def map_single(pool, formulas, fn):
        return reduce_by_eq(pool.map(fn, formulas))

    extended = sorted(formulas, key=attrgetter("name"))
    extended = reduce_with_similarity(extended, cached)

    with TaskExecutor(max_workers=num_workers) as pool:
        fliparood = map_multiple(pool, extended, recursive_fliparoo)
        extended.extend(fliparood)
        extended = reduce_with_similarity(extended, cached)

        switched = map_multiple(pool, extended, switch_signs)
        extended.extend(switched)
        extended = reduce_with_similarity(extended, cached)

        add_reduced = map_single(pool, extended, reduce_all_adds)
        extended.extend(add_reduced)
        extended = reduce_with_similarity(extended, cached)

        mul_expanded = map_single(pool, extended, expand_all_muls)
        extended.extend(mul_expanded)
        extended = reduce_with_similarity(extended, cached)

        np2_expanded = map_single(pool, extended, expand_all_nopower2_muls)
        extended.extend(np2_expanded)
        extended = reduce_with_similarity(extended, cached)

    return set(reduce_by_eq(extended))
