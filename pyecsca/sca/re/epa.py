"""
Provides functionality inspired by the Exceptional Procedure Attack [EPA]_.
"""

from typing import Callable, Literal, Union

from public import public

from pyecsca.ec.point import Point
from pyecsca.sca.re.rpa import MultipleContext


@public
def errors_out(
    ctx: MultipleContext,
    out: Point,
    check_funcs: dict[str, Callable],
    check_condition: Union[Literal["all"], Literal["necessary"]],
    precomp_to_affine: bool,
) -> bool:
    """

    :param ctx: The context containing the points and formulas.
    :param out: The output point to check.
    :param check_funcs:
    :param check_condition:
    :param precomp_to_affine:
    :return:

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
    # This actually passes the multiple itself to the check, not the inputs(parents)
    for point in affine_points:
        if "affine" in check_funcs:
            func = check_funcs["affine"]
            if func(ctx.points[point]):
                return True
    # Now handle the regular checks
    for point in points:
        formula = ctx.formulas[point]
        if formula in check_funcs:
            func = check_funcs[formula]
            inputs = list(map(lambda pt: ctx.points[pt], ctx.parents[point]))
            if func(*inputs):
                return True
    return False
