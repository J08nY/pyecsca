from pyecsca.ec.op import CodeOp
from typing import Dict, Set
from ast import parse
from pyecsca.ec.op import OpType
from pyecsca.ec.formula_gen.formula_graph import *
from itertools import chain, combinations


def best_switch(formula, metric):
    best_formula = formula
    best_measure = metric(formula)
    for _,switched_formula in generate_switched_formulas(formula):
        new_measure = metric(switched_formula)
        if new_measure > best_measure:
            best_formula = switched_formula
            best_measure = new_measure
    return best_formula


def generate_switched_formulas(formula, rename = True):
    Gr = EFDFormulaGraph()
    Gr.construct_graph(formula, rename)
    subs = filter(lambda x: x not in Gr.roots and x.is_sub, Gr.nodes)
    for node_combination in list(powerset(subs)):
        try:
            new_f = switch_sign(Gr, node_combination).to_EFDFormula()
            # print("node_comb:",node_combination)
            yield node_combination,new_f
        except BadSignSwitch:
            continue


def switch_sign(Gr, node_combination):
    nodes_i = [Gr.node_index(node) for node in node_combination]
    Gr = deepcopy(Gr)
    node_combination = set(Gr.nodes[node_i] for node_i in nodes_i)
    output_signs = {out: 1 for out in Gr.output_names}
    for node in node_combination:
        change_sides(node)
        if node.output_node:
            output_signs[node.result] = -1

    queue = sum(
        [
            [(out, node.result) for out in node.outgoing_nodes]
            for node in node_combination
        ],
        [],
    )
    switched_subs = set()
    while queue:
        node, variable = queue.pop()
        queue = (
            switch_sign_propagate(node, variable, output_signs, switched_subs) + queue
        )

    # TODO rewrite this hacky solution:
    if Gr._formula.coordinate_model.name.startswith("jacobian"):
        output_signs = {out[0]: sign for out, sign in output_signs.items()}
        X, Y, Z = (output_signs[var] for var in ["X", "Y", "Z"])
        correct_output = X / (Z**2) == 1 and Y / (Z**3) == 1
    elif Gr._formula.coordinate_model.name.startswith("modified"):
        output_signs = {out[0]: sign for out, sign in output_signs.items()}
        X, Y, Z, T = (output_signs[var] for var in ["X", "Y", "Z", "T"])
        correct_output = X / (Z**2) == 1 and Y / (Z**3) == 1
        correct_output&= (T==1)
    else:
        correct_output = len(set(output_signs.values())) == 1
    if not correct_output:
        raise BadSignSwitch
    return Gr


class BadSignSwitch(Exception):
    pass


def switch_sign_propagate(node, variable, output_signs, switched_subs):
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
        switched_subs.add(node.result)
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


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))
