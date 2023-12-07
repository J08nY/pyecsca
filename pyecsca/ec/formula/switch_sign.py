from typing import Dict, Iterator, List
from ast import parse
from ..op import OpType, CodeOp
from .graph import EFDFormulaGraph, ConstantNode, Node, CodeOpNode
from itertools import chain, combinations
from .efd import EFDFormula


def generate_switched_formulas(
    formula: EFDFormula, rename=True
) -> Iterator[EFDFormula]:
    graph = EFDFormulaGraph(formula, rename)
    for node_combination in subnode_lists(graph):
        try:
            yield switch_sign(graph, node_combination).to_EFDFormula()
        except BadSignSwitch:
            continue


def subnode_lists(graph: EFDFormulaGraph):
    return powerlist(filter(lambda x: x not in graph.roots and x.is_sub, graph.nodes))


def switch_sign(graph: EFDFormulaGraph, node_combination) -> EFDFormulaGraph:
    nodes_i = [graph.node_index(node) for node in node_combination]
    graph = graph.deepcopy()
    node_combination = set(graph.nodes[node_i] for node_i in nodes_i)
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

    # TODO rewrite this hacky solution:
    if graph._formula.coordinate_model.name.startswith("jacobian"):
        output_signs = {out[0]: sign for out, sign in output_signs.items()}
        X, Y, Z = (output_signs[var] for var in ["X", "Y", "Z"])
        correct_output = X / (Z**2) == 1 and Y / (Z**3) == 1
    elif graph._formula.coordinate_model.name.startswith("modified"):
        output_signs = {out[0]: sign for out, sign in output_signs.items()}
        X, Y, Z, T = (output_signs[var] for var in ["X", "Y", "Z", "T"])
        correct_output = X / (Z**2) == 1 and Y / (Z**3) == 1
        correct_output &= T == 1
    else:
        correct_output = len(set(output_signs.values())) == 1
    if not correct_output:
        raise BadSignSwitch
    return graph


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
    assert node.is_mul or node.is_pow or node.is_inv or node.is_div
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
