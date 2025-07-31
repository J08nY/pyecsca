"""
Provides functionality inspired by the Exceptional Procedure Attack [EPA]_.
"""

from typing import Callable, Literal, Union

from public import public

from pyecsca.ec.point import Point
from pyecsca.sca.re.rpa import MultipleContext


@public
def graph_to_check_inputs(
    ctx: MultipleContext,
    out: Point,
    check_condition: Union[Literal["all"], Literal["necessary"]],
    precomp_to_affine: bool,
) -> dict[str, list[tuple[int, ...]]]:
    """
    Compute the inputs for the checks based on the context and output point. This function traverses the graph of points
    and collects the inputs for each formula type, in the form of tuples of input multiples. It also adds a special
    "affine" formula that checks the multiples of the points that need to be converted to affine coordinates. Which
    points this "affine" formula checks depends on the `precomp_to_affine` parameter.

    :param ctx: The context containing the points and formulas.
    :param out: The output point of the computation.
    :param check_condition: Whether to check all points or only those necessary for the output point.
    :param precomp_to_affine: Whether to include the precomputed points in the to-affine checks.
    :return: A dictionary mapping formula names to lists of tuples of input multiples.

    .. note::
        The scalar multiplier must not short-circuit.
    """
    affine_points = {out, *ctx.precomp.values()} if precomp_to_affine else {out}
    if check_condition == "all":
        points = set(ctx.points.keys())
    elif check_condition == "necessary":
        points = set(affine_points)
        queue = set(affine_points)
        while queue:
            point = queue.pop()
            for parent in ctx.parents[point]:
                points.add(parent)
                queue.add(parent)
    else:
        raise ValueError("check_condition must be 'all' or 'necessary'")
    # Special case the "to affine" transform and checks
    formula_checks: dict[str, list[tuple[int, ...]]] = {
        "affine": [(ctx.points[point],) for point in affine_points]
    }
    # This actually passes the multiple itself to the check, not the inputs(parents)
    # Now handle the regular checks
    for point in points:
        formula = ctx.formulas[point]
        inputs = tuple(map(lambda pt: ctx.points[pt], ctx.parents[point]))
        check_list = formula_checks.setdefault(formula, [])
        check_list.append(inputs)
    return formula_checks


@public
def evaluate_checks(
    check_funcs: dict[str, Callable], check_inputs: dict[str, list[tuple[int, ...]]]
) -> bool:
    """
    Evaluate the checks for each formula type based on the provided functions and inputs.

    :param check_funcs: The functions to apply for each formula type. There are two callable types:
        - `check(k, l, q)`, that gets applied to binary formulas (like `add`), where `k` and `l` are the input multiples
        of the base point and `q` is the base point order.
        - `check(k, q)`, that gets applied to unary formulas (like conversion to affine `affine`), where `k` is the input multiple
        of the base point and `q` is the base point order.
    :param check_inputs: A dictionary mapping formula names to lists of tuples of input multiples. The output of
        :func:`graph_to_check_inputs`.
    :return: Whether any of the checks returned True -> whether the computation errors out.

    .. note::
        The scalar multiplier must not short-circuit.
    """
    for name, func in check_funcs.items():
        if name not in check_inputs:
            continue
        for inputs in check_inputs[name]:
            if func(*inputs):
                return True
    return False


@public
def errors_out(
    ctx: MultipleContext,
    out: Point,
    check_funcs: dict[str, Callable],
    check_condition: Union[Literal["all"], Literal["necessary"]],
    precomp_to_affine: bool,
) -> bool:
    """
    Check whether the computation errors out based on the provided context, output point, and check functions.

    :param ctx: The context containing the points and formulas.
    :param out: The output point of the computation.
    :param check_funcs: The functions to apply for each formula type. There are two callable types:
        - `check(k, l, q)`, that gets applied to binary formulas (like `add`), where `k` and `l` are the input multiples
        of the base point and `q` is the base point order.
        - `check(k, q)`, that gets applied to unary formulas (like conversion to affine `affine`), where `k` is the input multiple
        of the base point and `q` is the base point order.
    :param check_condition: Whether to check all points or only those necessary for the output point.
    :param precomp_to_affine: Whether to include the precomputed points in the to-affine checks.
    :return: Whether any of the checks returned True -> whether the computation errors out.

    .. note::
        The scalar multiplier must not short-circuit.
    """
    formula_checks = graph_to_check_inputs(ctx, out, check_condition, precomp_to_affine)
    return evaluate_checks(check_funcs, formula_checks)
