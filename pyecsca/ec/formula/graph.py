"""Provides tools for working with formulas as graphs."""

import matplotlib.pyplot as plt
import networkx as nx
from ast import parse, Expression
from typing import Dict, List, Tuple, Set, Optional, MutableMapping, Any
from copy import deepcopy
from public import public
from abc import ABC, abstractmethod

from pyecsca.ec.formula.base import Formula
from pyecsca.ec.formula.code import CodeFormula
from pyecsca.ec.op import CodeOp, OpType


@public
class Node(ABC):
    def __init__(self):
        self.incoming_nodes = []
        self.outgoing_nodes = []
        self.output_node = False
        self.input_node = False

    @property
    @abstractmethod
    def label(self) -> str:
        pass

    @property
    @abstractmethod
    def result(self) -> str:
        pass

    @property
    def is_sub(self) -> bool:
        return False

    @property
    def is_mul(self) -> bool:
        return False

    @property
    def is_add(self) -> bool:
        return False

    @property
    def is_id(self) -> bool:
        return False

    @property
    def is_sqr(self) -> bool:
        return False

    @property
    def is_pow(self) -> bool:
        return False

    @property
    def is_inv(self) -> bool:
        return False

    @property
    def is_div(self) -> bool:
        return False

    @property
    def is_neg(self) -> bool:
        return False

    @abstractmethod
    def __repr__(self) -> str:
        pass

    def reconnect_outgoing_nodes(self, destination):
        destination.output_node = self.output_node
        for out in self.outgoing_nodes:
            out.incoming_nodes = [
                n if n != self else destination for n in out.incoming_nodes
            ]
            destination.outgoing_nodes.append(out)


@public
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
        return str(self.value)

    def __repr__(self) -> str:
        return f"Node({self.value})"


class CodeOpNode(Node):
    color = "#1f78b4"

    def __init__(self, op: CodeOp):
        super().__init__()
        self.op = op
        if self.op.operator not in [
            OpType.Sub,
            OpType.Add,
            OpType.Id,
            OpType.Sqr,
            OpType.Mult,
            OpType.Div,
            OpType.Pow,
            OpType.Inv,
            OpType.Neg,
        ]:
            raise ValueError

    @classmethod
    def from_str(cls, result: str, left, operator, right):
        opstr = f"{result} = {left if left is not None else ''}{operator.op_str}{right if right is not None else ''}"
        return cls(CodeOp(parse(opstr.replace("^", "**"))))

    @property
    def label(self) -> str:
        return f"{self.op.result}:{self.op.operator.op_str}"  # noqa

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


@public
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


def formula_input_variables(formula: Formula) -> List[str]:
    return (
        sorted(formula.inputs)
        + formula.parameters
        + formula.coordinate_model.curve_model.parameter_names
    )


@public
class FormulaGraph:
    coordinate_model: Any
    name: str
    shortname: str
    parameters: List[str]
    assumptions: List[Expression]
    nodes: List[Node]
    input_nodes: MutableMapping[str, InputNode]
    output_names: Set[str]
    roots: List[Node]

    def __init__(self, formula: Formula, rename=True):
        self.name = formula.name
        self.shortname = formula.shortname
        self.parameters = formula.parameters
        self.assumptions = formula.assumptions
        self.coordinate_model = formula.coordinate_model
        self.output_names = formula.outputs
        self.input_nodes = {v: InputNode(v) for v in formula_input_variables(formula)}
        self.roots = list(self.input_nodes.values())
        self.nodes = self.roots.copy()
        discovered_nodes: Dict[str, Node] = self.input_nodes.copy()  # type: ignore
        constants: Dict[int, Node] = {}
        for op in formula.code:
            code_node = CodeOpNode(op)
            for side in (op.left, op.right):
                if side is None:
                    continue
                if isinstance(side, int):
                    parent_node = constants.get(side, ConstantNode(side))
                    self.nodes.append(parent_node)
                    self.roots.append(parent_node)
                else:
                    parent_node = discovered_nodes[side]
                parent_node.outgoing_nodes.append(code_node)
                code_node.incoming_nodes.append(parent_node)
            self.nodes.append(code_node)
            discovered_nodes[op.result] = code_node
        # flag output nodes
        for output_name in self.output_names:
            discovered_nodes[output_name].output_node = True

        # go through the nodes and make sure that every node is root or has parents
        for node in self.nodes:
            if not node.incoming_nodes and node not in self.roots:
                self.roots.append(node)
        if rename:
            self.reindex()

    def node_index(self, node: Node) -> int:
        return self.nodes.index(node)

    def deepcopy(self):
        return deepcopy(self)

    def to_formula(self, name=None) -> CodeFormula:
        code = list(
            map(
                lambda x: deepcopy(x.op),  # type: ignore
                filter(lambda n: n not in self.roots, self.nodes),
            )
        )
        parameters = list(self.parameters)
        assumptions = [deepcopy(assumption) for assumption in self.assumptions]
        for klass in CodeFormula.__subclasses__():
            if klass.shortname == self.shortname:
                return klass(
                    self.name if name is None else self.name + "-" + name,
                    code,
                    self.coordinate_model,
                    parameters,
                    assumptions,
                )
        raise ValueError(f"Bad formula type: {self.shortname}")

    def networkx_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        for i, node in enumerate(self.nodes):
            graph.add_node(
                i, result=node.result, label=node.label, op=getattr(node, "op", None)
            )
        for node in self.nodes:
            for out in node.outgoing_nodes:
                graph.add_edge(self.node_index(node), self.node_index(out))
        return graph

    def levels(self) -> List[List[Node]]:
        stack = self.roots.copy()
        levels = [(n, 0) for n in stack]
        level_counter = 1
        while stack:
            tmp_stack = []
            while stack:
                node = stack.pop()
                levels.append((node, level_counter))
                for out in node.outgoing_nodes:
                    tmp_stack.append(out)
            stack = tmp_stack
            level_counter += 1
        # separate into lists

        level_lists: List[List[Node]] = [[] for _ in range(level_counter)]
        discovered = []
        for node, l in reversed(levels):
            if node not in discovered:
                level_lists[l].append(node)
                discovered.append(node)
        return level_lists

    def output_nodes(self) -> List[Node]:
        return list(filter(lambda x: x.output_node, self.nodes))

    def planar_positions(self) -> Dict[int, Tuple[float, float]]:
        positions = {}
        for i, level in enumerate(self.levels()):
            for j, node in enumerate(level):
                positions[self.node_index(node)] = (
                    0.1 * float(i**2) + 3 * float(j),
                    -6 * float(i),
                )
        return positions

    def draw(self, filename: Optional[str] = None, figsize: Tuple[int, int] = (12, 12)):
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
            for v in self.output_nodes():
                iv = self.node_index(v)
                index_paths.extend(sorted(nx.all_simple_paths(gnx, iu, iv)))
        paths = []
        for p in index_paths:
            paths.append([self.nodes[v] for v in p])
        return paths

    def reorder(self):
        self.nodes = sum(self.levels(), [])

    def remove_node(self, node):
        self.nodes.remove(node)
        if node in self.roots:
            self.roots.remove(node)
        for in_node in node.incoming_nodes:
            in_node.outgoing_nodes = list(
                filter(lambda x: x != node, in_node.outgoing_nodes)
            )
        for out_node in node.outgoing_nodes:
            out_node.incoming_nodes = list(
                filter(lambda x: x != node, out_node.incoming_nodes)
            )

    def add_node(self, node):
        if isinstance(node, ConstantNode):
            self.roots.append(node)
        self.nodes.append(node)

    def reindex(self):
        results: Dict[str, str] = {}
        counter = 0
        for node in self.nodes:
            if not isinstance(node, CodeOpNode):
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

    def update(self):
        self.reorder()
        self.reindex()

    def print(self):
        for node in self.nodes:
            print(node)


def rename_ivs(formula: Formula) -> CodeFormula:
    graph = FormulaGraph(formula)
    return graph.to_formula()
