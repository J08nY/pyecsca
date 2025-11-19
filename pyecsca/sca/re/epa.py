"""
Provides functionality inspired by the Exceptional Procedure Attack [EPA]_.
"""

from typing import Callable, Literal, Union, Optional

import matplotlib.pyplot as plt
import networkx as nx


from public import public

from pyecsca.ec.point import Point
from pyecsca.sca.re.rpa import MultipleContext


@public
def graph_to_check_inputs(
    precomp_ctx: MultipleContext,
    full_ctx: MultipleContext,
    out: Point,
    check_condition: Union[Literal["all"], Literal["necessary"]],
    precomp_to_affine: bool,
    use_init: bool = True,
    use_multiply: bool = True,
    check_formulas: Optional[set[str]] = None,
) -> dict[str, set[tuple[int, ...]]]:
    """
    Compute the inputs for the checks based on the context and output point. This function traverses the graph of points
    and collects the inputs for each formula type, in the form of tuples of input multiples. It also adds a special
    "affine" formula that checks the multiples of the points that need to be converted to affine coordinates. Which
    points this "affine" formula checks depends on the `precomp_to_affine` parameter.

    :param precomp_ctx: The context containing the points and formulas (precomputation phase).
    :param full_ctx: The context containing the points and formulas (full computation).
    :param out: The output point of the computation.
    :param check_condition: Whether to check all points or only those necessary for the output point.
    :param precomp_to_affine: Whether to include the precomputed points in the to-affine checks.
    :param use_init: Whether to consider the point multiples that happen in scalarmult initialization.
    :param use_multiply: Whether to consider the point multiples that happen in scalarmult multiply (after initialization).
    :param check_formulas: If provided, only formulas in this set will be considered for checks.
    :return: A dictionary mapping formula names to sets of tuples of input multiples.

    .. note::
        The scalar multiplier must not short-circuit.
    """
    if not use_init and not use_multiply:
        raise ValueError("At least one of use_init or use_multiply must be True.")

    affine_points: set[Point] = set()
    if use_init and use_multiply:
        affine_points = (
            {out, *precomp_ctx.precomp.values()} if precomp_to_affine else {out}
        )
    elif use_init:
        affine_points = {*precomp_ctx.precomp.values()} if precomp_to_affine else set()
    elif use_multiply:
        affine_points = {out}

    def _necessary(ctx, for_what):
        res = {out}
        queue = {*for_what}
        while queue:
            point = queue.pop()
            for parent in ctx.parents[point]:
                res.add(parent)
                queue.add(parent)
        return res

    points: set[Point] = set()
    if check_condition == "all":
        if use_init and use_multiply:
            points = set(full_ctx.points.keys())
        elif use_init:
            points = set(precomp_ctx.points.keys())
        elif use_multiply:
            points = set(full_ctx.points.keys()) - set(precomp_ctx.points.keys())
    elif check_condition == "necessary":
        if use_init and use_multiply:
            points = _necessary(full_ctx, affine_points)
        elif use_init:
            points = _necessary(full_ctx, affine_points) & set(
                precomp_ctx.points.keys()
            )
        elif use_multiply:
            points = _necessary(full_ctx, affine_points) - set(
                precomp_ctx.points.keys()
            )
    else:
        raise ValueError("check_condition must be 'all' or 'necessary'")
    # Special case the "to affine" transform and checks
    formula_checks: dict[str, set[tuple[int, ...]]] = {
        "affine": {(full_ctx.points[point],) for point in affine_points}
    }
    # This actually passes the multiple itself to the check, not the inputs(parents)
    # Now handle the regular checks

    def get_point(pt):
        return full_ctx.points[pt]

    for point in points:
        formula = full_ctx.formulas[point]
        if not formula or (
            check_formulas is not None and formula not in check_formulas
        ):
            # Skip input point or infty point (they magically appear and do not have an origin formula)
            continue
        inputs = tuple(map(get_point, full_ctx.parents[point]))
        check_list = formula_checks.setdefault(formula, set())
        check_list.add(inputs)
    return formula_checks


@public
def graph_plot(
    precomp_ctx: MultipleContext,
    full_ctx: MultipleContext,
    out: Point,
) -> plt.Figure:
    """
    Plot the computation graph, highlighting necessary points and precomputed points.

    Legend:
    - Circles: Necessary points in the computation.
    - Triangles: Unnecessary points in the computation.
    - Blue: Points computed during the full computation phase.
    - Red: Unnecessary points computed during the full computation phase (dummies).
    - Green: Points computed during the precomputation phase.
    - Cyan: Precomputed points (stored by the multiplier).

    :param precomp_ctx: The context containing the points and formulas (precomputation phase).
    :param full_ctx: The context containing the points and formulas (full computation).
    :param out: The output point of the computation.
    :return: The matplotlib figure object representing the graph.
    """
    graph = full_ctx.to_networkx()

    for layer, nodes in enumerate(nx.topological_generations(graph)):
        for node in nodes:
            graph.nodes[node]["layer"] = layer
    for node in graph.nodes():
        graph.nodes[node]["necessary"] = False
    queue = {out}
    while queue:
        node = queue.pop()
        graph.nodes[node]["necessary"] = True
        for n in graph.predecessors(node):
            queue.add(n)
    fig, ax = plt.subplots(figsize=(60, 10))
    pos = nx.multipartite_layout(graph, subset_key="layer")
    for point, p in pos.items():
        p[0] *= 0.15
        if not graph.nodes[point]["necessary"]:
            p[1] += 0.01
        if point in precomp_ctx.points.keys():
            if graph.nodes[point]["precomp"]:
                p[1] -= 0.01

    colors = {}
    necessary = []
    unnecessary = []
    for point in graph.nodes():
        if graph.nodes[point]["necessary"]:
            color = "#202080"
            necessary.append(point)
        else:
            color = "#802020"
            unnecessary.append(point)

        if point in precomp_ctx.points.keys():
            color = "#208020"
            if graph.nodes[point]["precomp"]:
                color = "#30a0a0"
        colors[point] = color

    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=necessary,
        ax=ax,
        node_color=[colors[pt] for pt in necessary],
        node_shape="o",
        node_size=500,
        margins=[0.1, 0.1],
    )
    nx.draw_networkx_nodes(
        graph,
        pos,
        nodelist=unnecessary,
        ax=ax,
        node_color=[colors[pt] for pt in unnecessary],
        node_shape="^",
        node_size=500,
        margins=[0.1, 0.1],
    )
    nx.draw_networkx_edges(graph, pos, ax=ax, connectionstyle="arc3,rad=0.05")
    nx.draw_networkx_edge_labels(
        graph,
        pos,
        ax=ax,
        edge_labels={(u, v): graph.edges[u, v]["formula"] for u, v in graph.edges()},
    )
    for p in pos.values():
        p[1] += 0.003
    nx.draw_networkx_labels(
        graph, pos, ax=ax, labels={n: graph.nodes[n]["multiple"] for n in graph.nodes()}
    )
    fig.tight_layout()
    return fig


@public
def evaluate_checks(
    check_funcs: dict[str, Union[Callable[[int, int], bool], Callable[[int], bool]]],
    check_inputs: dict[str, set[tuple[int, ...]]],
) -> bool:
    """
    Evaluate the checks for each formula type based on the provided functions and inputs.

    :param check_funcs: The functions to apply for each formula type. There are two callable types:
        - `check(k, l)`, that gets applied to binary formulas (like `add`), where `k` and `l` are the input multiples
        of the base point and `q` is the base point order.
        - `check(k)`, that gets applied to unary formulas (like conversion to affine `affine`), where `k` is the input multiple
        of the base point and `q` is the base point order.
    :param check_inputs: A dictionary mapping formula names to sets of tuples of input multiples. The output of
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
    precomp_ctx: MultipleContext,
    full_ctx: MultipleContext,
    out: Point,
    check_funcs: dict[str, Union[Callable[[int, int], bool], Callable[[int], bool]]],
    check_condition: Union[Literal["all"], Literal["necessary"]],
    precomp_to_affine: bool,
    use_init: bool = True,
    use_multiply: bool = True,
) -> bool:
    """
    Check whether the computation errors out based on the provided context, output point, and check functions.

    :param precomp_ctx: The context containing the points and formulas (precomputation phase).
    :param full_ctx: The context containing the points and formulas (full computation).
    :param out: The output point of the computation.
    :param check_funcs: The functions to apply for each formula type. There are two callable types:
        - `check(k, l)`, that gets applied to binary formulas (like `add`), where `k` and `l` are the input multiples
        of the base point and `q` is the base point order.
        - `check(k)`, that gets applied to unary formulas (like conversion to affine `affine`), where `k` is the input multiple
        of the base point and `q` is the base point order.
    :param check_condition: Whether to check all points or only those necessary for the output point.
    :param precomp_to_affine: Whether to include the precomputed points in the to-affine checks.
    :param use_init: Whether to consider the point multiples that happen in scalarmult initialization.
    :param use_multiply: Whether to consider the point multiples that happen in scalarmult multiply (after initialization).
    :return: Whether any of the checks returned True -> whether the computation errors out.

    .. note::
        The scalar multiplier must not short-circuit.
    """
    formula_checks = graph_to_check_inputs(
        precomp_ctx,
        full_ctx,
        out,
        check_condition,
        precomp_to_affine,
        use_init,
        use_multiply,
    )
    return evaluate_checks(check_funcs, formula_checks)
