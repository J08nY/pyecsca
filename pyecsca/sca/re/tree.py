"""
Tools for working with distinguishing maps and trees.

         ________
     ,o88~~88888888o,
   ,~~?8P  88888     8,
  d  d88 d88 d8_88     b
 d  d888888888          b
 8,?88888888  d8.b o.   8
 8~88888888~ ~^8888  db 8
 ?  888888          ,888P
  ?  `8888b,_      d888P
   `   8888888b   ,888'
     ~-?8888888 _.P-~
         ~~~~~~

Here we grow the trees.
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⢰⣆⠀⢿⢢⡀⠸⣱⡀⢀⢤⡶⡄⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⢰⣤⡴⣴⠢⣧⣿⢤⣈⠺⡧⣺⠷⡟⠓⠃⣇⢧⣶⣀⠀⠀⠀⠀⠀⠀
 ⠀⢀⡀⢠⠽⣇⣹⠓⠽⡌⠓⠹⢶⢿⠀⢠⠁⡈⡶⠓⠋⠙⢻⡹⢓⡶⠀⠀⠀
 ⠀⣬⣿⡎⠓⠒⠻⢄⡀⢳⡀⠀⢸⠈⢦⢸⠀⣸⢇⠀⢀⣠⡞⢉⣡⣴⣲⠄⠀
 ⢠⣽⣈⣇⣴⣲⠖⠀⠉⠚⠳⣄⢸⠀⠈⣿⠊⡼⡦⢏⠉⠀⠉⢙⠮⢱⡆⠀⠀
 ⠘⢎⡇⠘⢧⡀⣀⣤⣤⠄⠀⠈⢻⣇⢀⣽⠖⢣⣣⡤⠤⠒⠚⣝⣆⠀⠀⠀⠀
 ⠀⠀⠓⠢⠤⠽⢧⣀⠀⠀⠀⠀⠀⣿⠏⢹⡴⠋⠙⠒⠶⢖⢤⡀⢀⣤⣶⠗⠀
 ⡢⢄⠐⠮⠷⢆⠀⠈⠙⠛⠛⠻⢶⣿⠀⣾⢀⣀⣀⣤⠤⡼⡓⢋⣿⠫⢕⡆⠀
 ⠈⣻⠧⠤⠤⠤⠿⠗⠒⠒⠛⠶⣤⣿⣼⠛⠉⠙⠒⣶⡖⠳⡗⠺⡿⣤⣤⢄⡀
 ⠰⣹⠀⠀⠀⢟⡆⠀⠀⠀⠀⠀⠈⣿⡿⠀⠀⠀⠀⢧⠇⠀⠀⠀⠀⠙⠮⡯⠀
 ⠀⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣤⠾⠛⣿⠙⠛⠶⢦⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""
from math import ceil
from copy import deepcopy
from typing import Mapping, Any, Set, List, Tuple, Optional

import numpy as np
import pandas as pd
from public import public
from anytree import RenderTree, NodeMixin, AbstractStyle


@public
class Map:
    """A distinguishing map."""

    mapping: pd.DataFrame
    doman: List[Any]
    codomain: Set[Any]

    def __init__(self, mapping: pd.DataFrame, domain: List[Any], codomain: Set[Any]):
        self.mapping = mapping
        self.domain = domain
        self.codomain = codomain

    @classmethod
    def from_binary_sets(cls, cfgs: Set[Any], mapping: Mapping[Any, Set[Any]]):
        cfgs_l = list(cfgs)
        inputs_l = list(set().union(*mapping.values()))
        data = [[elem in mapping[cfg] for elem in inputs_l] for cfg in cfgs_l]
        return Map(pd.DataFrame(data, index=cfgs_l), inputs_l, {True, False})

    @classmethod
    def from_io_map(cls, cfgs: Set[Any], mapping: Mapping[Any, Mapping[Any, Any]]):
        cfgs_l = list(cfgs)
        inputs: Set[Any] = set()
        codomain: Set[Any] = set()
        for io_map in mapping.values():
            inputs.update(io_map.keys())
            codomain.update(io_map.values())
        inputs_l = list(inputs)
        data = [[mapping[cfg].get(elem, None) for elem in inputs_l] for cfg in cfgs_l]
        return Map(pd.DataFrame(data, index=cfgs_l), inputs_l, codomain)


@public
class Node(NodeMixin):
    """A node in a distinguishing tree."""

    cfgs: Set[Any]
    dmap_index: Optional[int]
    dmap_input: Optional[Any]
    response: Optional[Any]

    def __init__(
        self,
        cfgs: Set[Any],
        dmap_index: Optional[int] = None,
        dmap_input: Optional[Any] = None,
        response: Optional[Any] = None,
        parent=None,
        children=None,
    ):
        self.cfgs = cfgs
        self.dmap_index = dmap_index
        self.dmap_input = dmap_input
        self.response = response

        self.parent = parent
        if children:
            self.children = children


@public
class Tree:
    """A distinguishing tree."""

    maps: List[Map]
    root: Node

    def __init__(self, root: Node, *maps: Map):
        self.maps = list(maps)
        self.root = root

    @property
    def leaves(self) -> Tuple[Node]:
        return self.root.leaves

    @property
    def height(self) -> int:
        return self.root.height

    @property
    def size(self) -> int:
        return self.root.size

    def render(self) -> str:
        style = AbstractStyle("\u2502  ", "\u251c\u2500\u2500", "\u2514\u2500\u2500")

        def _str(n: Node):
            pre = f">{n.response} " if n.response is not None else ""
            if n.is_leaf:
                return pre + "\n".join(str(cfg) for cfg in n.cfgs)
            else:
                return pre + f"{n.dmap_index}({n.dmap_input})"

        return RenderTree(self.root, style=style).by_attr(_str)

    def describe(self) -> str:
        leaf_sizes = [len(leaf.cfgs) for leaf in self.leaves]
        leafs: List[int] = sum(([size] * size for size in leaf_sizes), [])
        return "\n".join(
            (
                f"Total cfgs: {len(self.root.cfgs)}",
                f"Depth: {self.height}",
                f"Leaf sizes: {sorted(leaf_sizes)}",
                f"Average leaf size: {np.mean(leaf_sizes):.3}",
                f"Mean result size: {np.mean(leafs):.3}",
            )
        )

    def expand(self, dmap: Map) -> "Tree":
        tree = deepcopy(self)
        tree.maps.append(dmap)
        for leaf in tree.leaves:
            expanded = _build_tree(leaf.cfgs, *tree.maps, response=leaf.response)
            # If we were able to split the leaf further, then replace it with the found tree.
            if not expanded.is_leaf:
                parent = leaf.parent
                leaf.parent = None
                expanded.parent = parent
        return tree

    @classmethod
    def build(cls, cfgs: Set[Any], *maps: Map) -> "Tree":
        return cls(_build_tree(cfgs, *maps), *maps)


def _degree(split: pd.Series) -> float:
    return len(split)


def _size_of_largest(split: pd.Series) -> float:
    return max(split)


def _average_size(split: pd.Series) -> float:
    return sum(split**2) / sum(split)


def _build_tree(cfgs: Set[Any], *maps: Map, response: Optional[Any] = None) -> Node:
    # If there is only one remaining cfg, we do not need to continue and just return (base case 1).
    # Note that n_cfgs will never be 0 here, as the base case 2 returns if the cfgs cannot
    # be split into two sets (one would be empty).
    n_cfgs = len(cfgs)
    ncfgs = set(cfgs)
    if n_cfgs == 1:
        return Node(ncfgs, response=response)

    # Go over the maps and figure out which one splits the best.
    best_distinguishing_column = None
    best_distinguishing_dmap = None
    best_restricted = None
    best_score = None
    for dmap in maps:
        # Now we have a map, it may be binary or have larger output domain
        # Note we should look at the restriction of the map to the current "cfgs" and split those
        restricted = dmap.mapping.loc[list(cfgs), :]  # .filter(items=cfgs, axis=0)
        for i, column in restricted.items():
            split = column.value_counts(dropna=False)
            # XXX: Try the other scores.
            score = _size_of_largest(split)
            if best_score is None or score < best_score:
                best_distinguishing_column = i
                best_distinguishing_dmap = dmap
                best_score = score
                best_restricted = restricted
            # Early abort if optimal score is hit. The +1 is for "None" values which are not in the codomain.
            if score == ceil(n_cfgs / (len(dmap.codomain) + 1)):
                break

    best_distinguishing_element = best_distinguishing_dmap.domain[best_distinguishing_column]
    # Now we have a dmap as well as an element in it that splits the best.
    # Go over the groups of configs that share the response
    groups = best_restricted.groupby(best_distinguishing_column, dropna=False)  # type: ignore
    # We found nothing distinguishing the configs, so return them all (base case 2).
    if groups.ngroups == 1:
        return Node(ncfgs, response=response)

    # Create our node
    dmap_index = maps.index(best_distinguishing_dmap)
    result = Node(ncfgs, dmap_index, best_distinguishing_element, response=response)

    for output, group in groups:
        child = _build_tree(set(group.index), *maps, response=output)
        child.parent = result

    return result
