from typing import List, Any, Generator
from ast import parse
from public import public
from copy import deepcopy

from pyecsca.ec.formula.base import Formula
from pyecsca.ec.op import OpType, CodeOp
from pyecsca.ec.formula.graph import (
    FormulaGraph,
    CodeOpNode,
    ConstantNode,
    Node,
    CodeFormula,
)
from pyecsca.ec.formula.fliparoo import find_fliparoos, AddFliparoo, MulFliparoo


@public
def reduce_all_adds(formula: Formula, rename=True) -> CodeFormula:
    graph = FormulaGraph(formula, rename=rename)
    add_fliparoos = find_single_input_add_fliparoos(graph)
    for add_fliparoo in add_fliparoos:
        reduce_add_fliparoo(add_fliparoo, copy=False)
    reduce_all_XplusX(graph)
    mul_fliparoos = find_constant_mul_fliparoos(graph)
    for mul_fliparoo in mul_fliparoos:
        reduce_mul_fliparoo(mul_fliparoo, copy=False)
    return graph.to_formula("reduce_add")


@public
def expand_all_muls(formula: Formula, rename=True) -> CodeFormula:
    graph = FormulaGraph(formula, rename)
    enodes = find_expansion_nodes(graph)
    for enode in enodes:
        expand_mul(graph, enode, copy=False)
    return graph.to_formula("expand_mul")


@public
def expand_all_nopower2_muls(formula: Formula, rename=True) -> CodeFormula:
    graph = FormulaGraph(formula, rename)
    enodes = find_expansion_nodes(graph, nopower2=True)
    for enode in enodes:
        expand_mul(graph, enode, copy=False)
    return graph.to_formula("expand_np2mul")


def find_single_input_add_fliparoos(graph: FormulaGraph) -> List[AddFliparoo]:
    fliparoos = find_fliparoos(graph, AddFliparoo)
    single_input_fliparoos = []
    for fliparoo in fliparoos:
        found = False
        for i in range(len(fliparoo), 1, -1):
            subfliparoo = fliparoo.slice(0, i)
            if len(set(subfliparoo.input_nodes())) == 1:
                found = True
                break
        if found:
            s = subfliparoo.slice(0, i)
            single_input_fliparoos.append(s)
    return single_input_fliparoos


def find_constant_mul_fliparoos(graph: FormulaGraph) -> List[MulFliparoo]:
    fliparoos = find_fliparoos(graph, MulFliparoo)
    constant_mul_fliparoo = []
    for fliparoo in fliparoos:
        found = False
        for i in range(len(fliparoo), 1, -1):
            subfliparoo = fliparoo.slice(0, i)
            nonconstant_inputs = list(
                filter(
                    lambda x: not isinstance(x, ConstantNode), subfliparoo.input_nodes()
                )
            )
            if len(nonconstant_inputs) != 1:
                continue
            inode = nonconstant_inputs[0]
            if inode not in fliparoo.first.incoming_nodes:
                continue
            if not sum(
                1
                for node in fliparoo.first.incoming_nodes
                if isinstance(node, ConstantNode)
            ):
                continue
            found = True
            break
        if found:
            s = subfliparoo.slice(0, i)
            constant_mul_fliparoo.append(s)
    return constant_mul_fliparoo


def find_expansion_nodes(graph: FormulaGraph, nopower2=False) -> List[Node]:
    expansion_nodes: List[Node] = []
    for node in graph.nodes:
        if not isinstance(node, CodeOpNode) or not node.is_mul:
            continue
        for par in node.incoming_nodes:
            if isinstance(par, ConstantNode):
                if nopower2 and is_power_of_2(par.value):
                    continue
                expansion_nodes.append(node)
                break
    return expansion_nodes


def is_power_of_2(n: int) -> bool:
    while n > 1:
        if n & 1 == 1:
            return False
        n >>= 1
    return True


def reduce_all_XplusX(graph: FormulaGraph):
    adds = find_all_XplusX(graph)
    for node in adds:
        reduce_XplusX(graph, node)
    graph.update()


def find_all_XplusX(graph) -> List[CodeOpNode]:
    adds = []
    for node in graph.nodes:
        if not isinstance(node, CodeOpNode) or not node.is_add:
            continue
        if node.incoming_nodes[0] == node.incoming_nodes[1]:
            adds.append(node)
    return adds


def reduce_XplusX(graph: FormulaGraph, node: CodeOpNode):
    inode = node.incoming_nodes[0]
    const_node = ConstantNode(2)
    node.incoming_nodes[1] = const_node
    const_node.outgoing_nodes = [node]
    graph.add_node(const_node)
    inode.outgoing_nodes = list(filter(lambda x: x != node, inode.outgoing_nodes))
    inode.outgoing_nodes.append(node)
    opstr = f"{node.result} = {inode.result}{OpType.Mult.op_str}{const_node.value}"
    node.op = CodeOp(parse(opstr))


def reduce_mul_fliparoo(fliparoo: MulFliparoo, copy=True):
    if copy:
        fliparoo = fliparoo.deepcopy()

    first, last = fliparoo.first, fliparoo.last
    inode = next(
        filter(lambda x: not isinstance(x, ConstantNode), first.incoming_nodes)
    )
    const_nodes: List[ConstantNode] = [
        node for node in fliparoo.input_nodes() if isinstance(node, ConstantNode)
    ]
    sum_const_node = ConstantNode(sum(v.value for v in const_nodes))
    fliparoo.graph.add_node(sum_const_node)

    inode.outgoing_nodes = [n if n != first else last for n in inode.outgoing_nodes]
    last.incoming_nodes = [inode, sum_const_node]
    sum_const_node.outgoing_nodes = [last]

    opstr = f"{last.result} = {inode.result}{OpType.Mult.op_str}{sum_const_node.value}"
    last.op = CodeOp(parse(opstr))

    for node in fliparoo:
        if node == last:
            continue
        fliparoo.graph.remove_node(node)

    for node in const_nodes:
        if not node.outgoing_nodes:
            fliparoo.graph.remove_node(node)

    fliparoo.graph.update()

    return fliparoo.graph


def reduce_add_fliparoo(fliparoo: AddFliparoo, copy=True):
    if copy:
        fliparoo = fliparoo.deepcopy()
    first, last = fliparoo.first, fliparoo.last
    par = first.incoming_nodes[0]
    const_node = ConstantNode(len(fliparoo) + 1)
    fliparoo.graph.add_node(const_node)
    mul_node = CodeOpNode.from_str(
        last.result, const_node.result, OpType.Mult, par.result
    )
    fliparoo.graph.add_node(mul_node)
    mul_node.incoming_nodes = [const_node, par]
    par.outgoing_nodes.append(mul_node)
    const_node.outgoing_nodes.append(mul_node)
    mul_node.output_node = last.output_node
    last.reconnect_outgoing_nodes(mul_node)
    for node in fliparoo:
        fliparoo.graph.remove_node(node)

    fliparoo.graph.update()

    return fliparoo.graph


def expand_mul(graph: FormulaGraph, node: Node, copy=True) -> FormulaGraph:
    if copy:
        i = graph.node_index(node)
        graph = deepcopy(graph)
        node = graph.nodes[i]

    const_par = next(filter(lambda x: isinstance(x, ConstantNode), node.incoming_nodes))
    par = next(filter(lambda x: not isinstance(x, ConstantNode), node.incoming_nodes))
    initial_node = CodeOpNode.from_str(node.result, par.result, OpType.Add, par.result)
    graph.add_node(initial_node)
    initial_node.incoming_nodes = [par, par]
    par.outgoing_nodes.extend([initial_node, initial_node])
    prev_node = initial_node
    for _ in range(const_par.value - 2):
        anode = CodeOpNode.from_str(
            node.result, prev_node.result, OpType.Add, par.result
        )
        anode.incoming_nodes = [prev_node, par]
        par.outgoing_nodes.append(anode)
        graph.add_node(anode)
        prev_node.outgoing_nodes = [anode]
        prev_node = anode

    prev_node.output_node = node.output_node
    node.reconnect_outgoing_nodes(prev_node)
    graph.remove_node(node)
    graph.remove_node(const_par)
    graph.update()

    return graph


class Partition:
    value: int
    parts: List["Partition"]

    def __init__(self, n: int):
        self.value = n
        self.parts = []

    @property
    def is_final(self):
        return not self.parts

    def __repr__(self):
        if self.is_final:
            return f"({self.value})"
        l, r = self.parts
        return f"({l.__repr__()},{r.__repr__()})"

    def __add__(self, other):
        a = Partition(self.value + other.value)
        a.parts = [self, other]
        return a

    def __eq__(self, other):
        if self.value != other.value:
            return False
        if self.is_final or other.is_final:
            return self.is_final == other.is_final
        l, r = self.parts
        lo, ro = other.parts
        return (l == lo and r == ro) or (l == ro and r == lo)

    # unhashable at the moment
    __hash__ = None  # type: ignore


def compute_partitions(n: int) -> List[Partition]:
    partitions = [Partition(n)]
    for d in range(1, n // 2 + 1):
        n_d = n - d
        for partition_dp in compute_partitions(d):
            for partition_n_dp in compute_partitions(n_d):
                partitions.append(partition_dp + partition_n_dp)
    # remove duplicates
    result = []
    for p in partitions:
        if p not in result:
            result.append(p)
    return result


@public
def generate_partitioned_formulas(formula: Formula, rename=True):
    graph = FormulaGraph(formula, rename)
    enodes = find_expansion_nodes(graph)
    for i, enode in enumerate(enodes):
        for j, part_graph in enumerate(generate_all_node_partitions(graph, enode)):
            yield part_graph.to_formula(f"partition[{i},{j}]")


def generate_all_node_partitions(
    original_graph: FormulaGraph, node: Node
) -> Generator[FormulaGraph, Any, None]:
    const_par = next(filter(lambda x: isinstance(x, ConstantNode), node.incoming_nodes))
    const_par_value = const_par.value

    par = next(filter(lambda x: not isinstance(x, ConstantNode), node.incoming_nodes))
    i, ic, ip = (
        original_graph.node_index(node),
        original_graph.node_index(const_par),
        original_graph.node_index(par),
    )

    for partition in compute_partitions(const_par_value):
        if partition.is_final:
            continue

        # copy
        graph = deepcopy(original_graph)
        node, const_par, par = graph.nodes[i], graph.nodes[ic], graph.nodes[ip]
        graph.remove_node(const_par)
        lresult, rresult = f"{node.result}L", f"{node.result}R"
        empty_left_node = CodeOpNode.from_str(lresult, "PART", OpType.Add, "PART")
        empty_right_node = CodeOpNode.from_str(rresult, "PART", OpType.Add, "PART")
        addition_node = CodeOpNode.from_str(node.result, lresult, OpType.Add, rresult)
        graph.add_node(empty_left_node)
        graph.add_node(empty_right_node)
        graph.add_node(addition_node)
        addition_node.outgoing_nodes = node.outgoing_nodes
        addition_node.output_node = node.output_node
        addition_node.incoming_nodes = [empty_left_node, empty_right_node]
        empty_left_node.outgoing_nodes = [addition_node]
        empty_right_node.outgoing_nodes = [addition_node]

        left, right = partition.parts
        partition_node(graph, empty_left_node, left, par)
        partition_node(graph, empty_right_node, right, par)

        graph.remove_node(node)
        graph.update()
        yield graph


def partition_node(
    graph: FormulaGraph, node: CodeOpNode, partition: Partition, source_node: Node
):
    if partition.is_final and partition.value == 1:
        # source node will take the role of node
        # note: node has precisely one output node, since it was created during partitions
        assert len(node.outgoing_nodes) == 1
        child = node.outgoing_nodes[0]
        source_node.outgoing_nodes.append(child)

        left, right = child.incoming_nodes[0].result, child.incoming_nodes[1].result
        if child.incoming_nodes[0] == node:
            left = source_node.result
            child.incoming_nodes[0] = source_node
        else:
            right = source_node.result
            child.incoming_nodes[1] = source_node
        opstr = f"{child.result} = {left}{child.optype.op_str}{right}"
        child.op = CodeOp(parse(opstr))
        graph.remove_node(node)
        return

    if partition.is_final:
        source_node.outgoing_nodes.append(node)
        const_node = ConstantNode(partition.value)
        graph.add_node(const_node)
        opstr = (
            f"{node.result} = {source_node.result}{OpType.Mult.op_str}{partition.value}"
        )
        node.op = CodeOp(parse(opstr))
        node.incoming_nodes = [source_node, const_node]
        const_node.outgoing_nodes = [node]
        return

    lresult, rresult = f"{node.result}L", f"{node.result}R"
    empty_left_node = CodeOpNode.from_str(lresult, "PART", OpType.Add, "PART")
    empty_right_node = CodeOpNode.from_str(rresult, "PART", OpType.Add, "PART")

    opstr = f"{node.result} = {lresult}{OpType.Add.op_str}{rresult}"
    node.op = CodeOp(parse(opstr))
    graph.add_node(empty_left_node)
    graph.add_node(empty_right_node)

    node.incoming_nodes = [empty_left_node, empty_right_node]
    empty_left_node.outgoing_nodes = [node]
    empty_right_node.outgoing_nodes = [node]

    left, right = partition.parts
    partition_node(graph, empty_left_node, left, source_node)
    partition_node(graph, empty_right_node, right, source_node)
