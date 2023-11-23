from pyecsca.ec.op import CodeOp
from typing import Dict, Set
from ast import parse
from pyecsca.ec.op import OpType
from pyecsca.ec.formula_gen.formula_graph import *


def greedy_fliparoo(formula, metric):
    original_state = metric(formula)
    before_fliparoo = deepcopy(formula)
    counter = 0
    while True:
        before_fliparoo_state = metric(before_fliparoo)
        max_fliparood = before_fliparoo
        max_fliparood_state = before_fliparoo_state
        for _,fliparood in generate_fliparood_formulas(before_fliparoo):
            after_fliparoo_state = metric(fliparood)
            if after_fliparoo_state > max_fliparood_state:
                max_fliparood = fliparood
                max_fliparood_state = after_fliparoo_state
        if max_fliparood_state <= before_fliparoo_state:
            break
        counter += 1
        before_fliparoo = max_fliparood
    return counter, before_fliparoo, metric(before_fliparoo)


def brute_force_fliparoo(formula, metric, depth):
    found = recursive_fliparoo(formula, depth)
    measured = [(num_f, flip_f, metric(flip_f)) for num_f, flip_f in found]
    measured = list(filter(lambda x: x[0] > 0, measured))
    best_found = max(measured, key=lambda x: x[2])
    if best_found[2] == metric(formula):
        return None
    return best_found


def recursive_fliparoo(formula, depth=3):
    all_fliparoos = [([], formula)]
    counter = 0
    while depth > counter:
        counter += 1
        flips = []
        for chains, fliped_formula in all_fliparoos:
            rename = counter==1 # rename ivs before first fliparoo
            for chain,fliparood in generate_fliparood_formulas(fliped_formula, rename):
                flips.append((chains+[chain], fliparood))
        all_fliparoos.extend(flips)
    return all_fliparoos


def generate_fliparood_formulas(formula, rename = True):
    Gr = EFDFormulaGraph()
    Gr.construct_graph(formula, rename)
    chains = find_fliparoo_chains(Gr)
    for chain in generate_subchains(chains):
        if chain[0].is_mul:
            yield chain, make_fliparoo(Gr, chain, 0).to_EFDFormula()
            yield tuple(reversed(chain)), make_fliparoo(Gr, chain, 1).to_EFDFormula()
        if chain[0].is_add or chain[0].is_sub:
            try:
                yield chain, make_fliparoo_sub(Gr, chain, 0).to_EFDFormula()
            except BadFliparoo:
                pass
            try:
                yield tuple(reversed(chain)), make_fliparoo_sub(Gr, chain, 1).to_EFDFormula()
            except BadFliparoo:
                pass


def find_fliparoo_chains(graph: EFDFormulaGraph) -> Set[Tuple[Node]]:

    # find largest operation chain
    fliparoos = set()
    for ilong_path in graph.find_all_paths():
        long_path = ilong_path[1:]  # get rid of the input variables
        chain = largest_fliparoo_chain(long_path)
        if chain:
            fliparoos.add(chain)

    # remove duplicities and chains in inclusion
    fliparoos = sorted(fliparoos, key=len, reverse=True)
    longest_fliparoos = set()
    for fliparoo in fliparoos:
        if not is_subfliparoo(fliparoo, longest_fliparoos):
            longest_fliparoos.add(fliparoo)
    return longest_fliparoos


def generate_subchains(chains):
    for chain in chains:
        l = len(chain)
        for i in range(l):
            for j in range(i + 2, l + 1):
                yield chain[i:j]


def is_subfliparoo(fliparoo: Tuple[Node], longest_fliparoos: Set[Tuple[Node]]) -> bool:
    for other_fliparoo in longest_fliparoos:
        l1, l2 = len(fliparoo), len(other_fliparoo)
        for i in range(l2 - l1):
            if other_fliparoo[i : i + l1] == fliparoo:
                return True
    return False


def largest_fliparoo_chain(chain: List[Node]) -> Tuple[Node]:
    for i in range(len(chain) - 1):
        for j in range(len(chain) - 1, i, -1):
            subchain = chain[i : j + 1]
            if is_fliparoo_chain(subchain):
                return tuple(subchain)
    return ()


def is_fliparoo_chain(nodes: List[Node]) -> bool:
    for i, node in enumerate(nodes[:-1]):
        if node.outgoing_nodes != [nodes[i + 1]]:
            return False
        if node.output_node:
            return False
    operations = set(node.op.operator for node in nodes)
    if operations == set([OpType.Mult]):
        return True
    if operations.issubset(set([OpType.Add, OpType.Sub])):
        return True
    return False


def make_fliparoo(
    graph: EFDFormulaGraph, chain: List[Node], side: bool
) -> EFDFormulaGraph:
    i0, i1, i1par = (
        graph.node_index(chain[0]),
        graph.node_index(chain[-1]),
        graph.node_index(chain[-2]),
    )
    graph = deepcopy(graph)
    node0, node1, node1par = graph.nodes[i0], graph.nodes[i1], graph.nodes[i1par]

    node0par = node0.incoming_nodes[side]
    node1par2_side = 1 - node1.incoming_nodes.index(node1par)
    node1par = node1.incoming_nodes[node1par2_side]

    node0.op = opcode_fliparoo(node0.op, node0par.result, node1par.result, side=side)
    node1.op = opcode_fliparoo(
        node1.op, node1par.result, node0par.result, side=node1par2_side
    )

    node0par.outgoing_nodes.remove(node0)
    node1par.outgoing_nodes.remove(node1)
    node0par.outgoing_nodes.append(node1)
    node1par.outgoing_nodes.append(node0)
    node0.incoming_nodes[side] = node1par
    node1.incoming_nodes[node1par2_side] = node0par

    graph.reorder()
    # print(node0.result,node1.result)
    return graph


class BadFliparoo(Exception):
    pass


def make_fliparoo_sub(
    graph: EFDFormulaGraph, chain: List[Node], side: bool
) -> EFDFormulaGraph:
    i0, i1, i1par = (
        graph.node_index(chain[0]),
        graph.node_index(chain[-1]),
        graph.node_index(chain[-2]),
    )
    graph = deepcopy(graph)
    node0, node1, node1par = graph.nodes[i0], graph.nodes[i1], graph.nodes[i1par]

    node0par = node0.incoming_nodes[side]
    node1par2_side = 1 - node1.incoming_nodes.index(node1par)
    node1par2 = node1.incoming_nodes[node1par2_side]

    if side == 0 and node1par2_side == 0:
        sign_diff = sum(1 for node in chain[1:] if node.is_sub) % 2
        if sign_diff:
            raise BadFliparoo
        node0.op = opcode_fliparoo(
            node0.op, node0par.result, node1par2.result, side=side
        )
        node1.op = opcode_fliparoo(
            node1.op, node1par2.result, node0par.result, side=node1par2_side
        )
    elif side == 1 and node1par2_side == 1:
        sign_diff = sum(1 for node in chain if node.is_sub) % 2
        node0.op = opcode_fliparoo(
            node0.op,
            node0par.result,
            node1par2.result,
            side=side,
            switch_sign=sign_diff,
        )
        node1.op = opcode_fliparoo(
            node1.op,
            node1par2.result,
            node0par.result,
            side=node1par2_side,
            switch_sign=sign_diff,
        )
    elif side == 0 and node1par2_side == 1:
        sign_diff = sum(1 for node in chain[1:] if node.is_sub) % 2
        if sign_diff:
            raise BadFliparoo
        node0.op = opcode_fliparoo(
            node0.op, node0par.result, node1par2.result, side=side
        )
        node1.op = opcode_fliparoo(
            node1.op, node1par2.result, node0par.result, side=node1par2_side
        )
    elif side == 1 and node1par2_side == 0:
        sign_diff = sum(1 for node in chain if node.is_sub) % 2
        if sign_diff:
            raise BadFliparoo
        node0.op = opcode_fliparoo(
            node0.op, node0par.result, node1par2.result, side=side
        )
        node1.op = opcode_fliparoo(
            node1.op, node1par2.result, node0par.result, side=node1par2_side
        )

    node0par.outgoing_nodes.remove(node0)
    node1par2.outgoing_nodes.remove(node1)
    node0par.outgoing_nodes.append(node1)
    node1par2.outgoing_nodes.append(node0)
    node0.incoming_nodes[side] = node1par2
    node1.incoming_nodes[node1par2_side] = node0par

    graph.reorder()
    # print(node0.result,node1.result)
    return graph


def opcode_fliparoo(op, orig_var, new_var, side=int, switch_sign=False):
    result, left, operator, right = op.result, op.left, op.operator.op_str, op.right
    if side == 0:
        left = new_var
    if side == 1:
        right = new_var
    if switch_sign and op.operator == OpType.Add:
        operator = OpType.Sub.op_str
    if switch_sign and op.operator == OpType.Sub:
        operator = OpType.Add.op_str
    opstr = f"{result} = {left if left is not None else ''}{operator}{right if right is not None else ''}"
    return CodeOp(parse(opstr.replace("^", "**")))
