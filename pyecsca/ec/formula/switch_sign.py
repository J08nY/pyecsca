from typing import Dict, Iterator, List, Any
from ast import parse
from public import public
from itertools import chain, combinations

from pyecsca.ec.op import OpType, CodeOp
from pyecsca.ec.formula.base import Formula
from pyecsca.ec.formula.graph import FormulaGraph, ConstantNode, CodeOpNode, CodeFormula
from pyecsca.ec.point import Point
from pyecsca.ec.mod import Mod, mod


@public
def generate_switched_formulas(formula: Formula, rename=True) -> Iterator[CodeFormula]:
    graph = FormulaGraph(formula, rename)
    for i, node_combination in enumerate(subnode_lists(graph)):
        try:
            yield switch_sign(graph, node_combination).to_formula(f"switch[{i}]")
        except BadSignSwitch:
            continue


def subnode_lists(graph: FormulaGraph):
    return powerlist(filter(lambda x: x not in graph.roots and x.is_sub, graph.nodes))


def switch_sign(graph: FormulaGraph, node_combination) -> FormulaGraph:
    nodes_i = [graph.node_index(node) for node in node_combination]
    graph = graph.deepcopy()
    node_combination = {graph.nodes[node_i] for node_i in nodes_i}
    output_signs = {out: 1 for out in graph.output_names}

    queue = []
    for node in node_combination:
        change_sides(node)
        if node.output_node:
            output_signs[node.result] = -1
        queue.extend([(out, node.result) for out in node.outgoing_nodes])

    while queue:
        node, variable = queue.pop()
        queue = switch_sign_propagate(node, variable, output_signs) + queue

    sign_test(output_signs, graph.coordinate_model)
    return graph


def sign_test(output_signs: Dict[str, int], coordinate_model: Any):
    scale = coordinate_model.formulas.get("z", None)
    if scale is None:
        scale = coordinate_model.formulas.get("scale", None)
    p = 7
    out_inds = set(map(lambda x: "".join([o for o in x if o.isdigit()]), output_signs))
    for ind in out_inds:
        point_dict = {}
        for out, sign in output_signs.items():
            if not out.endswith(ind):
                continue
            out_var = out[: out.index(ind)]
            if not out_var.isalpha():
                continue
            point_dict[out_var] = mod(sign, p)
        point = Point(coordinate_model, **point_dict)
        try:
            apoint = point.to_affine()
        except NotImplementedError:
            # Ignore switch signs if we cannot test them.
            if scale is None:
                raise BadSignSwitch
            apoint = scale(p, point)[0]
        if set(apoint.coords.values()) != {mod(1, p)}:
            raise BadSignSwitch


class BadSignSwitch(Exception):
    pass


def switch_sign_propagate(
    node: CodeOpNode, variable: str, output_signs: Dict[str, int]
):
    if node.is_add:
        if variable == node.incoming_nodes[1].result:
            node.op = change_operator(node.op, OpType.Sub)
            return []
        change_sides(node)
        node.op = change_operator(node.op, OpType.Sub)
        return []
    if node.is_id or node.is_neg:
        output_signs[node.result] *= -1
        return [(child, node.result) for child in node.outgoing_nodes]

    if node.is_sqr:
        return []
    if node.is_sub:
        if node.incoming_nodes[0].result == variable:
            node.op = change_operator(node.op, OpType.Add)
            if node.output_node:
                output_signs[node.result] *= -1
            return [(child, node.result) for child in node.outgoing_nodes]
        node.op = change_operator(node.op, OpType.Add)
        return []
    if node.is_pow:
        exponent = next(
            filter(lambda n: isinstance(n, ConstantNode), node.incoming_nodes)
        )
        if exponent.value % 2 == 0:
            return []
    if node.output_node:
        output_signs[node.result] *= -1
    if not (node.is_mul or node.is_pow or node.is_inv or node.is_div):
        raise ValueError
    return [(child, node.result) for child in node.outgoing_nodes]


def change_operator(op, new_operator):
    result, left, right = op.result, op.left, op.right
    opstr = f"{result} = {left if left is not None else ''}{new_operator.op_str}{right if right is not None else ''}"
    return CodeOp(parse(opstr.replace("^", "**")))


def change_sides(node):
    op = node.op
    result, left, operator, right = op.result, op.left, op.operator.op_str, op.right
    left, right = right, left
    opstr = f"{result} = {left if left is not None else ''}{operator}{right if right is not None else ''}"
    node.op = CodeOp(parse(opstr.replace("^", "**")))
    node.incoming_nodes[1], node.incoming_nodes[0] = (
        node.incoming_nodes[0],
        node.incoming_nodes[1],
    )


def powerlist(iterable: Iterator) -> List:
    s = list(iterable)
    return list(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))
