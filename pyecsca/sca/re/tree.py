from copy import deepcopy
from typing import Mapping, Any, Set, List
from collections import Counter
from public import public
from anytree import Node


@public
def build_distinguishing_tree(
    cfgs: Set[Any], *cfg2resp_maps: Mapping[Any, Set[Any]], **kwargs
) -> Node:
    """
    Build a distinguishing tree for given mappings of configs to True oracle responses.

    :param cfgs: The configurations to distinguish.
    :param cfg2resp_maps: The mappings of configs to sets of inputs that give True oracle responses.
    :param kwargs: Additional keyword arguments that will be passed to the node.
    :return: A distinguishing tree.
    """
    n_cfgs = len(cfgs)
    # If there is only one remaining cfg, we do not need to continue and just return (base case 1).
    # Note that n_cfgs will never be 0 here, as the base case 2 returns if the cfgs cannot be split into two sets (one would be empty).
    if n_cfgs == 1:
        return Node(None, cfgs=set(cfgs), **kwargs)

    # Go over the maps and have a counter for each one
    counters: List[Counter] = [Counter() for cfg2resp in cfg2resp_maps]
    for counter, cfg2resp in zip(counters, cfg2resp_maps):
        for cfg in cfgs:
            elements = cfg2resp[cfg]
            counter.update(elements)

    nhalf = n_cfgs / 2
    best_distinguishing_map = None
    best_distinguishing_element = None
    best_count = None
    best_nhalf_distance = None
    for i, (counter, cfg2resp) in enumerate(zip(counters, cfg2resp_maps)):
        for multiple, count in counter.items():
            if (
                best_distinguishing_element is None
                or abs(count - nhalf) < best_nhalf_distance
            ):
                best_distinguishing_map = i
                best_distinguishing_element = multiple
                best_count = count
                best_nhalf_distance = abs(count - nhalf)

    # We found nothing distinguishing the configs, so return them all (base case 2).
    if best_count in (0, n_cfgs, None) or best_distinguishing_map is None:
        return Node(None, cfgs=set(cfgs), **kwargs)

    result = Node(
        (best_distinguishing_map, best_distinguishing_element), cfgs=set(cfgs), **kwargs
    )
    # Now go deeper and split based on the best-distinguishing element.
    true_cfgs = set(
        cfg
        for cfg in cfgs
        if best_distinguishing_element in cfg2resp_maps[best_distinguishing_map][cfg]
    )
    true_restricted_cfg2resps = [
        {cfg: cfg2resp[cfg] for cfg in true_cfgs} for cfg2resp in cfg2resp_maps
    ]
    true_child = build_distinguishing_tree(
        true_cfgs, *true_restricted_cfg2resps, oracle_response=True
    )
    true_child.parent = result

    false_cfgs = cfgs.difference(true_cfgs)
    false_restricted_cfg2resps = [
        {cfg: cfg2resp[cfg] for cfg in false_cfgs} for cfg2resp in cfg2resp_maps
    ]
    false_child = build_distinguishing_tree(
        false_cfgs, *false_restricted_cfg2resps, oracle_response=False
    )
    false_child.parent = result
    return result


def expand_tree(tree: Node, cfg2resp: Mapping[Any, Set[Any]]) -> Node:
    """
    Attempt to expand a given distinguishing tree with a new mapping of configs to True oracle responses.

    :param tree: The tree to expand (will be copied).
    :param cfg2resp: The new map.
    :return: The expanded tree.
    """
    tree = deepcopy(tree)
    for leaf in tree.leaves:
        expanded = build_distinguishing_tree(leaf.cfgs, cfg2resp)
        # If we were able to split the leaf further, then replace it with the found tree.
        if not expanded.is_leaf:
            leaf.name = expanded.name
            leaf.children = expanded.children
    return tree
