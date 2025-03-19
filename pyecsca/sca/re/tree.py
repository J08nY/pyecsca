"""
Tools for working with distinguishing maps and trees.

::

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

::

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

from math import ceil, log2
from copy import deepcopy
from typing import Mapping, Any, Set, List, Tuple, Optional, Dict, Union

import numpy as np
import pandas as pd
from public import public
from anytree import RenderTree, NodeMixin, AbstractStyle, PreOrderIter

from pyecsca.misc.utils import log


@public
class Map:
    """
    A distinguishing map.

    ::

                              domain
                              ======
                             ┌───┬───┬───┬───┬───┬───┐
                             │P1 │P2 │P3 │P4 │P5 │P5 │
                             └───┴───┴───┴───┴───┴───┘
                               :   :   :   :   :   :
                               :   :   :   :   :   :
                               :   :   :   :   :   :
                               :   :   :   :   :   :
         cfg_map     mapping ┌───┬───┬───┬───┬───┬───┐   codomain
         =======     ======= │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │   ========
        ┌────┬───┐       ┌───┼───┼───┼───┼───┼───┼───┤
        │cfg1│  0│:::::::│  0│ T │ F │ T │ F │ T │ T │   {T, F}
        ├────┼───┤       ├───┼───┼───┼───┼───┼───┼───┤
        │cfg2│  1│:::::::│  1│ F │ F │ F │ F │ T │ T │
        ├────┼───┤       ├───┼───┼───┼───┼───┼───┼───┤
        │cfg3│  2│:::::::│  2│ T │ T │ F │ F │ T │ T │
        └────┴───┘       └───┴───┴───┴───┴───┴───┴───┘

    """

    mapping: pd.DataFrame
    """
    A dataframe containing the map outputs.

    Both the columns and the index are simply numeric.
    The columns are the domain. The items in the rows are from the codomain.
    The index may have gaps. To map it back into the set of configs for each
    unique row, see the cfg_map.
    """
    cfg_map: pd.DataFrame
    """
    A dataframe containing the map from the cfgs to the index (integers).
    """
    domain: List[Any]
    """
    The (ordered) domain of the mapping.
    """
    codomain: Set[Any]
    """
    The (unordered) codomain of the mapping.
    """

    def __init__(
        self,
        mapping: pd.DataFrame,
        cfg_map: pd.DataFrame,
        domain: List[Any],
        codomain: Set[Any],
    ):
        self.mapping = mapping
        self.cfg_map = cfg_map
        self.domain = domain
        self.codomain = codomain

    @classmethod
    def from_sets(
        cls, cfgs: Set[Any], mapping: Mapping[Any, Set[Any]], deduplicate: bool = False
    ):
        """
        Build a distinguishing map with binary outputs from a set of configs and a mapping.

        Given configs {a, b, c} and a mapping of {a: {1}, b: {1, 2}, c: {2}}, this will
        build a distinguishing map with the following structure:

        ::

                                  domain
                                  ======
                                 ┌───┬───┐
                                 │ 1 │ 2 │
                                 └───┴───┘
                                   :   :
                                   :   :
                                   :   :
                                   :   :
             cfg_map     mapping ┌───┬───┐   codomain
             =======     ======= │ 0 │ 1 │   ========
            ┌────┬───┐       ┌───┼───┼───┤
            │ a  │  0│:::::::│  0│ T │ F │   {T, F}
            ├────┼───┤       ├───┼───┼───┤
            │ b  │  1│:::::::│  1│ T │ T │
            ├────┼───┤       ├───┼───┼───┤
            │ c  │  2│:::::::│  2│ F │ T │
            └────┴───┘       └───┴───┴───┘

        :param cfgs: The set of configs.
        :param mapping: The mapping from configs to a subset of inputs for which the oracle returns True.
        :param deduplicate: Whether to deduplicate the rows of the map.
        :return: The distinguishing map.
        """
        if deduplicate:
            hash2cfg: Dict[int, Set[Any]] = {}
            hash2val: Dict[int, Set[Any]] = {}
            inputs = set()
            for cfg, val in mapping.items():
                inputs.update(val)
                # TODO: Note this may cause collisions?
                h = hash(tuple(sorted(map(hash, val))))
                if hash2val.setdefault(h, val) != val:
                    raise ValueError("Collision in dedup!")
                hcfgs = hash2cfg.setdefault(h, set())
                hcfgs.add(cfg)
            cfgs_l: List[Any] = []
            cfgs_i = []
            cfgs_vals = []
            for i, (h, hcfgs) in enumerate(hash2cfg.items()):
                cfgs_l.extend(hcfgs)
                cfgs_i.extend([i] * len(hcfgs))
                cfgs_vals.append(hash2val[h])
            cfg_map = pd.DataFrame(cfgs_i, index=cfgs_l, columns=["vals"])
            inputs_l = list(inputs)
            data = [[elem in val for elem in inputs_l] for val in cfgs_vals]
        else:
            cfgs_l = list(cfgs)
            cfg_map = pd.DataFrame(
                list(range(len(cfgs_l))), index=cfgs_l, columns=["vals"]
            )
            inputs = set()
            for val in mapping.values():
                inputs.update(val)
            inputs_l = list(inputs)
            data = [[elem in mapping[cfg] for elem in inputs_l] for cfg in cfgs_l]
        return Map(pd.DataFrame(data), cfg_map, inputs_l, {True, False})

    @classmethod
    def from_io_maps(cls, cfgs: Set[Any], mapping: Mapping[Any, Mapping[Any, Any]]):
        """
        Build a distinguishing map with arbitrary outputs from a set of configs and a mapping
        that gives the oracle responses for each config and input.

        Given configs {a, b, c} and a mapping of {a: {x: 1, y: 2}, b: {x: 2, y: 1}, c: {x: 1}},
        this will build a distinguishing map with the following structure:

        ::

                                  domain
                                  ======
                                 ┌───┬───┐
                                 │ x │ y │
                                 └───┴───┘
                                   :   :
                                   :   :
                                   :   :
                                   :   :
             cfg_map     mapping ┌───┬───┐   codomain
             =======     ======= │ 0 │ 1 │   ========
            ┌────┬───┐       ┌───┼───┼───┤
            │ a  │  0│:::::::│  0│ 1 │ 2 │   {1, 2}
            ├────┼───┤       ├───┼───┼───┤
            │ b  │  1│:::::::│  1│ 2 │ 1 │
            ├────┼───┤       ├───┼───┼───┤
            │ c  │  2│:::::::│  2│ 1 │ - │
            └────┴───┘       └───┴───┴───┘

        :param cfgs: The set of configs.
        :param mapping: The mapping from configs to a mapping from inputs to outputs.
        :return: The distinguishing map.
        """
        cfgs_l = list(cfgs)
        cfg_map = pd.DataFrame(list(range(len(cfgs_l))), index=cfgs_l, columns=["vals"])
        inputs: Set[Any] = set()
        codomain: Set[Any] = set()
        has_na = False
        for io_map in mapping.values():
            new = set(io_map.keys())
            if inputs and new != inputs:
                # Map of some cfg doesn't have some inputs, we will fill in None.
                has_na = True
            inputs.update(new)
            codomain.update(io_map.values())
        if has_na:
            codomain.add(None)
        inputs_l = list(inputs)
        data = [[mapping[cfg].get(elem, None) for elem in inputs_l] for cfg in cfgs_l]
        return Map(pd.DataFrame(data), cfg_map, inputs_l, codomain)

    @property
    def cfgs(self) -> Set[Any]:
        """The set of configs in this distinguishing map."""
        return set(self.cfg_map.index)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            cfg, inp = item
            row = self.cfg_map.loc[[cfg], "vals"].iloc[0]
            col = self.domain.index(inp)
            return self.mapping.loc[row, col]
        else:
            raise KeyError

    def deduplicate(self):
        """Deduplicate the configs of this distinguishing map based on the rows."""
        indices = []

        def agg(thing):
            indices.append(thing.index)
            return thing.iloc[0]

        self.mapping = self.mapping.groupby(
            self.mapping.columns.tolist(), as_index=False, dropna=False
        ).agg(agg)
        new_cfg_map = self.cfg_map.copy()
        for i, index in enumerate(indices):
            new_cfg_map.loc[self.cfg_map["vals"].isin(index), "vals"] = i
        self.cfg_map = new_cfg_map

    def merge(self, other: "Map"):
        """
        Merge in another distinguishing map operating on different configs.

        :param other: The other distinguishing map.
        """
        # Domains should be equal (but only as sets, we can reorder)
        if set(self.domain) != set(other.domain):
            raise ValueError("Cannot merge dmaps with different domains.")
        reordering = [other.domain.index(elem) for elem in self.domain]
        # Get the last used index in cfg_map
        last = max(self.cfg_map["vals"])
        # Offset the other cfg_map and mapping index by last + 1
        other_cfg_map = other.cfg_map + (last + 1)
        other_mapping = other.mapping[reordering].set_index(
            other.mapping.index + (last + 1)
        )
        # Now concat the cfg_map and mapping
        self.cfg_map = pd.concat([self.cfg_map, other_cfg_map], copy=False)
        self.mapping = pd.concat([self.mapping, other_mapping], copy=False)
        # Finally, adjust the codomain
        self.codomain.update(other.codomain)

    def describe(self) -> str:
        """
        Describe some important properties of the distinguishing map.

        :return: A string with the description.
        """
        return "\n".join(
            (
                f"Total configs: {len(self.cfg_map)}, ({self.cfg_map.memory_usage(index=True).sum():_} bytes)",
                f"Rows: {len(self.mapping)}, ({self.mapping.memory_usage(index=True).sum():_} bytes)",
                f"Inputs: {len(self.domain)}",
                f"Codomain: {len(self.codomain)}",
                f"None in codomain: {None in self.codomain}",
            )
        )


@public
class Node(NodeMixin):
    """A node in a distinguishing tree."""

    cfgs: Set[Any]
    """Set of configs associated with this node."""
    response: Optional[Any]
    """The response to the *previous* oracle call that resulted in this node."""
    dmap_index: Optional[int]
    """The dmap index to be used for the oracle call for this node."""
    dmap_input: Optional[Any]
    """The input for the oracle call for this node (is from dmap at dmap_index in the Tree)."""

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

    def __hash__(self):
        return hash((Node, tuple(sorted(map(hash, self.cfgs)))))

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return (
            self.cfgs == other.cfgs
            and self.dmap_index == other.dmap_index
            and self.dmap_input == other.dmap_input
            and self.response == other.response
        )


@public
class SplitCriterion:
    """
    A splitting criterion to be used in tree building.
    """

    def __call__(self, split: pd.Series) -> float:
        """
        Compute the score of a split.

        :param split: The split to score.
        :return: The score, can be any (consistent) scale.
        """
        raise NotImplementedError

    def is_better(self, score: float, current_best: float) -> bool:
        """Whether the score is better than the current best."""
        raise NotImplementedError

    def is_optimal(self, score: float, n_cfgs: int, n_codomain: int) -> bool:
        """Whether the score is optimal and no further splits need to be examined."""
        raise NotImplementedError


class Degree(SplitCriterion):
    def __call__(self, split: pd.Series) -> float:
        # We want to maximize the number of groups.
        # The score is optimal if it is equal to min(n_cfgs, len(dmap.codomain)).
        return len(split)

    def is_better(self, score: float, current_best: float) -> bool:
        return score > current_best

    def is_optimal(self, score: float, n_cfgs: int, n_codomain: int) -> bool:
        return score == min(n_cfgs, n_codomain)


class SizeOfLargest(SplitCriterion):
    def __call__(self, split: pd.Series) -> float:
        # We want to minimize size of largest group.
        # The score is optimal if it is equal to ceil(n_cfgs / len(dmap.codomain)).
        return max(split)

    def is_better(self, score: float, current_best: float) -> bool:
        return score < current_best

    def is_optimal(self, score: float, n_cfgs: int, n_codomain: int) -> bool:
        return score == ceil(n_cfgs / n_codomain)


class AverageSize(SplitCriterion):
    def __call__(self, split: pd.Series) -> float:
        # We want to minimize the average size of the groups.
        # The score is optimal if it is equal to ceil(n_cfgs / len(dmap.codomain)).
        return sum(split**2) / sum(split)

    def is_better(self, score: float, current_best: float) -> bool:
        return score < current_best

    def is_optimal(self, score: float, n_cfgs: int, n_codomain: int) -> bool:
        return score == ceil(n_cfgs / n_codomain)


@public
class Tree:
    """A distinguishing tree."""

    maps: List[Map]
    """A list of dmaps. Nodes index into this when choosing which oracle to use."""
    root: Node
    """A root of the tree."""

    def __init__(self, root: Node, *maps: Map):
        self.maps = list(maps)
        self.root = root

    @property
    def leaves(self) -> Tuple[Node]:
        """Get the leaves of the tree as a tuple."""
        return self.root.leaves

    @property
    def height(self) -> int:
        """Get the height of the tree (distance from the root to the deepest leaf)."""
        return self.root.height

    @property
    def size(self) -> int:
        """Get the size of the tree (number of nodes)."""
        return self.root.size

    @property
    def precise(self) -> bool:
        """Whether the tree is precise (all leaves have only a single configuration)."""
        return all(len(leaf.cfgs) == 1 for leaf in self.leaves)

    def render(self) -> str:
        """
        Render the tree.

        :return: A string with the tree.
        """
        style = AbstractStyle("\u2502  ", "\u251c\u2500\u2500", "\u2514\u2500\u2500")

        def _str(n: Node):
            pre = f">{n.response} " if n.response is not None else ""
            if n.is_leaf:
                return pre + "\n".join(str(cfg) for cfg in n.cfgs)
            else:
                return pre + f"{n.dmap_index}({n.dmap_input})"

        return RenderTree(self.root, style=style).by_attr(_str)

    def render_basic(self) -> str:
        """
        Render the tree in a basic form, with number of configs as nodes.

        :return: A string with the tree.
        """
        return RenderTree(self.root).by_attr(lambda node: str(len(node.cfgs)))

    def describe(self) -> str:
        """
        Describe some important properties of the tree.

        :return: A string with the description.
        """
        lsize = log2(self.size)
        leaf_sizes = [len(leaf.cfgs) for leaf in self.leaves]
        leaf_depths = [leaf.depth for leaf in self.leaves]
        avg_leaf_depth = np.mean(leaf_depths)
        avg_leaf_size = np.mean(leaf_sizes)
        leafs_wsize: List[int] = sum(([size] * size for size in leaf_sizes), [])
        leafs_wdepth: List[int] = sum(
            ([depth] * size for size, depth in zip(leaf_sizes, leaf_depths)), []
        )
        mean_res_depth = np.mean(leafs_wdepth)
        mean_res_size = np.mean(leafs_wsize)
        balance = (
            "\n".join(
                (
                    "\nBalancedness:",
                    f"\theight/log2(size) = {self.height / lsize:.3f}",
                    f"\tavg_leaf_depth/log2(size) = {avg_leaf_depth / lsize:.3f}",
                    f"\tmean_res_depth/log2(size) = {mean_res_depth / lsize:.3f}",
                )
            )
            if all(len(dmap.codomain) == 2 for dmap in self.maps)
            else ""
        )
        probs = {self.root: 1.0}
        for node in PreOrderIter(self.root):
            if node.is_leaf:
                continue
            proba = probs[node]
            children = node.children
            n = len(children)
            for child in children:
                probs[child] = proba / n
        random_walk_depth = sum(probs[leaf] * leaf.depth for leaf in self.leaves)
        random_walk_size = sum(probs[leaf] * len(leaf.cfgs) for leaf in self.leaves)
        return (
            "\n".join(
                (
                    f"Dmaps: {len(self.maps)}",
                    f"Total cfgs: {len(self.root.cfgs)}",
                    f"Height: {self.height}",
                    f"Size: {self.size}",
                    f"Leaves: {len(leaf_sizes)}",
                    f"Precise: {self.precise}",
                    f"Leaf sizes: {sorted(leaf_sizes)}",
                    f"Leaf depths: {sorted(leaf_depths)}",
                    f"Average leaf depth: {avg_leaf_depth:.3f}",
                    f"Average leaf size: {avg_leaf_size:.3f}",
                    f"Random walk leaf depth: {random_walk_depth:.3f}",
                    f"Random walk leaf size: {random_walk_size:.3f}",
                    f"Mean result depth: {mean_res_depth:.3f}",
                    f"Mean result size: {mean_res_size:.3f}",
                )
            )
            + balance
        )

    def expand(self, dmap: Map) -> "Tree":
        """
        Expand a tree with a new distinguishing map.

        :param dmap: The distinguishing map to expand the tree with.
        """
        tree = Tree(deepcopy(self.root), *self.maps, dmap)
        for leaf in tree.leaves:
            expanded = _build_tree(
                leaf.cfgs, {len(self.maps): dmap}, response=leaf.response
            )
            # If we were able to split the leaf further, then replace it with the found tree.
            if not expanded.is_leaf:
                parent = leaf.parent
                leaf.parent = None
                expanded.parent = parent
        return tree

    @classmethod
    def build(cls, cfgs: Set[Any], *maps: Map, split: Union[str, SplitCriterion] = "largest") -> "Tree":
        """
        Build a tree.

        :param cfgs: The set of configs to build the tree for.
        :param maps: The distinguishing maps to use.
        :param split: The split criterion to use. Can be one of "degree", "largest", "average".
        :return: The tree.
        """
        return cls(_build_tree(cfgs, dict(enumerate(maps)), split=split), *maps)


def _build_tree(
    cfgs: Set[Any],
    maps: Mapping[int, Map],
    response: Optional[Any] = None,
    depth: int = 0,
    split: Union[str, SplitCriterion] = "largest",
) -> Node:
    pad = " " * depth
    # If there is only one remaining cfg, we do not need to continue and just return (base case 1).
    # Note that n_cfgs will never be 0 here, as the base case 2 returns if the cfgs cannot
    # be split into two sets (one would be empty).
    n_cfgs = len(cfgs)
    log(pad + f"Splitting {n_cfgs}.")
    cfgset = set(cfgs)
    if n_cfgs == 1:
        log(pad + "Trivial.")
        return Node(cfgset, response=response)

    # Choose the split criterion
    criterion: SplitCriterion
    if split == "degree":
        criterion = Degree()
    elif split == "largest":
        criterion = SizeOfLargest()
    elif split == "average":
        criterion = AverageSize()
    elif isinstance(split, SplitCriterion):
        criterion = split
    else:
        raise ValueError(f"Unknown split criterion: {split}")

    # Go over the maps and figure out which one splits the best.
    best_i = None
    best_dmap = None
    best_restricted = None
    best_column = None
    best_score = None
    for i, dmap in maps.items():
        # Now we have a map, it may be binary or have larger output domain
        # Note we should look at the restriction of the map to the current "cfgs" and split those
        restricted = dmap.mapping.loc[dmap.cfg_map.loc[list(cfgs), "vals"]]
        for j, column in restricted.items():
            counts = column.value_counts(dropna=False)
            score = criterion(counts)
            if best_score is None or criterion.is_better(score, best_score):
                best_i = i
                best_column = j
                best_dmap = dmap
                best_score = score
                best_restricted = restricted
            # Early abort if optimal score is hit.
            if criterion.is_optimal(score, n_cfgs, len(dmap.codomain)):
                break
    # We found nothing distinguishing the configs, so return them all (base case 2).
    if best_column is None or best_dmap is None:
        log(pad + "Nothing could split.")
        return Node(cfgset, response=response)

    best_distinguishing_element = best_dmap.domain[best_column]
    # Now we have a dmap as well as an element in it that splits the best.
    # Go over the groups of configs that share the response
    groups = best_restricted.groupby(best_column, dropna=False)  # type: ignore
    # We found nothing distinguishing the configs, so return them all (base case 2).
    if groups.ngroups == 1:
        log(pad + "Trivial split.")
        return Node(cfgset, response=response)

    # Create our node
    dmap_index = best_i
    result = Node(cfgset, dmap_index, best_distinguishing_element, response=response)

    # Go over the distinct group
    for output, group in groups:
        # Lookup the cfgs in the group
        group_cfgs = set(
            best_dmap.cfg_map.index[best_dmap.cfg_map["vals"].isin(group.index)]
        )
        log(pad + f"Split {len(group_cfgs)} via dmap {best_i}.")
        # And build the tree recursively
        child = _build_tree(group_cfgs, maps, response=output, depth=depth + 1)
        child.parent = result

    return result
