from pyecsca.ec.formula import EFDFormula
from pyecsca.ec.op import CodeOp, OpType
import matplotlib.pyplot as plt
import networkx as nx
import functools
from ast import parse
from typing import Dict, List, Tuple, Set
from copy import deepcopy
from abc import ABC, abstractmethod


class Node(ABC):
    def __init__(self):
        self.incoming_nodes = []
        self.outgoing_nodes = []
        self.output_node = False
        self.input_node = False

    @abstractmethod
    def label(self) -> str:
        pass

    @abstractmethod
    def result(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class ConstantNode(Node):

    color = "#b41f44"

    def __init__(self, i: int):
        super().__init__()
        self.value = i

    @property
    def label(self) -> str:
        return str(self.value)

    @property
    def result(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Node({self.name})"


class CodeOpNode(Node):

    color = "#1f78b4"

    def __init__(self, op: CodeOp):
        super().__init__()
        self.op = op
        assert self.op.operator in [
            OpType.Sub,
            OpType.Add,
            OpType.Id,
            OpType.Sqr,
            OpType.Mult,
            OpType.Div,
            OpType.Pow,
            OpType.Inv,
            OpType.Neg,
        ], self.op.operator

    @property
    def label(self) -> str:
        return f"{self.op.result}:{self.op.operator.op_str}"

    @property
    def result(self) -> str:
        return str(self.op.result)

    @property
    def optype(self) -> OpType:
        return self.op.operator

    @property
    def is_sub(self) -> bool:
        return self.optype == OpType.Sub

    @property
    def is_mul(self) -> bool:
        return self.optype == OpType.Mult

    @property
    def is_add(self) -> bool:
        return self.optype == OpType.Add

    @property
    def is_id(self) -> bool:
        return self.optype == OpType.Id

    @property
    def is_sqr(self) -> bool:
        return self.optype == OpType.Sqr

    @property
    def is_pow(self) -> bool:
        return self.optype == OpType.Pow

    @property
    def is_inv(self) -> bool:
        return self.optype == OpType.Inv

    @property
    def is_div(self) -> bool:
        return self.optype == OpType.Div

    @property
    def is_neg(self) -> bool:
        return self.optype == OpType.Neg

    def __repr__(self) -> str:
        return f"Node({self.op})"


class InputNode(Node):

    color = "#b41f44"

    def __init__(self, input: str):
        super().__init__()
        self.input = input
        self.input_node = True

    @property
    def label(self) -> str:
        return self.input

    @property
    def result(self) -> str:
        return self.input

    def __repr__(self) -> str:
        return f"Node({self.input})"


def formula_input_variables(formula: EFDFormula) -> List[str]:
    return (
        list(formula.inputs)
        + formula.parameters
        + formula.coordinate_model.curve_model.parameter_names
    )


class EFDFormulaGraph:
    def __init__(self):
        self.nodes: List = None
        self.input_nodes: Dict = None
        self.output_names: Set = None
        self.roots: List = None

    def construct_graph(self, formula: EFDFormula, rename = True):
        self._formula = formula  # TODO remove, its here only for to_EFDFormula
        self.output_names = formula.outputs
        self.input_nodes = {v: InputNode(v) for v in formula_input_variables(formula)}
        self.roots = list(self.input_nodes.values())
        self.nodes = self.roots.copy()
        discovered_nodes = self.input_nodes.copy()
        for op in formula.code:
            node = CodeOpNode(op)
            for side in (op.left, op.right):
                if side is None:
                    continue
                if isinstance(side, int):
                    parent_node = ConstantNode(side)
                    self.nodes.append(parent_node)
                    self.roots.append(parent_node)
                else:
                    parent_node = discovered_nodes[side]
                parent_node.outgoing_nodes.append(node)
                node.incoming_nodes.append(parent_node)
            self.nodes.append(node)
            discovered_nodes[op.result] = node
        # flag output nodes
        for output_name in self.output_names:
            discovered_nodes[output_name].output_node = True

        # go through the nodes and make sure that every node is root or has parents
        for node in self.nodes:
            if not node.incoming_nodes and not node in self.roots:
                self.roots.append(node)
        if rename:
            self.reindex()

    def node_index(self, node: CodeOpNode) -> int:
        return self.nodes.index(node)

    def to_EFDFormula(self) -> EFDFormula:
        # TODO rewrite
        new_graph = deepcopy(self)
        new_formula = new_graph._formula
        new_formula.code = list(
            map(
                lambda x: x.op,
                filter(lambda n: n not in new_graph.roots, new_graph.nodes),
            )
        )
        return new_formula

    @functools.cache
    def networkx_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        vertices = list(range(len(self.nodes)))
        graph.add_nodes_from(vertices)
        stack = self.roots.copy()
        while stack:
            node = stack.pop()
            for out in node.outgoing_nodes:
                stack.append(out)
                graph.add_edge(self.node_index(node), self.node_index(out))
        return graph

    def levels(self) -> List[List[Node]]:
        stack = self.roots.copy()
        levels = {n: 0 for n in stack}
        level_counter = 1
        while stack:
            tmp_stack = []
            while stack:
                node = stack.pop()
                levels[node] = level_counter
                for out in node.outgoing_nodes:
                    tmp_stack.append(out)
            stack = tmp_stack
            level_counter += 1
        # separate into lists

        level_lists = [[] for _ in range(level_counter)]
        for node, l in levels.items():
            level_lists[l].append(node)
        return level_lists

    @functools.cache
    def ending_nodes(self) -> List[Node]:
        return list(filter(lambda x: not x.outgoing_nodes, self.nodes))

    def planar_positions(self) -> Dict[int, Tuple[float, float]]:
        positions = {}
        for i, level in enumerate(self.levels()):
            for j, node in enumerate(level):
                positions[self.node_index(node)] = (
                    0.1 * float(i**2) + 3 * float(j),
                    -6 * float(i),
                )
        return positions

    def draw(self, filename: str = None, figsize: Tuple[int, int] = (12, 12)):
        gnx = self.networkx_graph()
        pos = nx.rescale_layout_dict(self.planar_positions())
        plt.figure(figsize=figsize)
        colors = [self.nodes[n].color for n in gnx.nodes]
        labels = {n: self.nodes[n].label for n in gnx.nodes}
        nx.draw(gnx, pos, node_color=colors, node_size=2000, labels=labels)
        if filename:
            plt.savefig(filename)
            plt.close()
        else:
            plt.show()

    def find_all_paths(self) -> List[List[Node]]:
        gnx = self.networkx_graph()
        index_paths = []
        for u in self.roots:
            iu = self.node_index(u)
            for v in self.ending_nodes():
                iv = self.node_index(v)
                index_paths.extend(nx.all_simple_paths(gnx, iu, iv))
        paths = []
        for p in index_paths:
            paths.append([self.nodes[v] for v in p])
        return paths

    def reorder(self):
        self.nodes = sum(self.levels(), [])

    def reindex(self):
        results = {}
        counter = 0
        for node in self.nodes:
            if node.input_node or isinstance(node, ConstantNode):
                continue
            op = node.op
            result, left, operator, right = (
                op.result,
                op.left,
                op.operator.op_str,
                op.right,
            )
            if left in results:
                left = results[left]
            if right in results:
                right = results[right]
            if not node.output_node:
                new_result = f"iv{counter}"
                counter += 1
            else:
                new_result = result
            opstr = f"{new_result} = {left if left is not None else ''}{operator}{right if right is not None else ''}"
            results[result] = new_result
            node.op = CodeOp(parse(opstr.replace("^", "**")))

    def print(self):
        for node in self.nodes:
            print(node)


def rename_ivs(formula: EFDFormula):
    graph = EFDFormulaGraph()
    graph.construct_graph(formula)
    return graph.to_EFDFormula()