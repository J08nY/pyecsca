from typing import Mapping, Any, Set
from collections import Counter
from public import public
from anytree import Node


@public
def build_distinguishing_tree(
    cfg2resp: Mapping[Any, Set[Any]], **kwargs
) -> Node:
    """
    Build a distinguishing tree for a given mapping of configs to True oracle responses.

    :param cfg2resp:
    :param kwargs:
    :return:
    """
    n_cfgs = len(cfg2resp)
    # If there is only one remaining cfg, we do not need to continue and just return (base case 1).
    # Note that n_cfgs will never be 0 here, as the base case 2 returns if the cfgs cannot be split into two sets (one would be empty).
    if n_cfgs == 1:
        return Node(None, cfgs=list(cfg2resp.keys()), **kwargs)

    counts: Counter = Counter()
    for elements in cfg2resp.values():  # Elements of the set need to be hashable
        counts.update(elements)

    nhalf = n_cfgs / 2
    best_distinguishing_element = None
    best_count = None
    best_nhalf_distance = None
    for multiple, count in counts.items():
        if (
            best_distinguishing_element is None
            or abs(count - nhalf) < best_nhalf_distance
        ):
            best_distinguishing_element = multiple
            best_count = count
            best_nhalf_distance = abs(count - nhalf)

    # We found nothing distinguishing the configs, so return them all (base case 2).
    if best_count in (0, n_cfgs, None):
        return Node(None, cfgs=list(cfg2resp.keys()), **kwargs)

    result = Node(
        best_distinguishing_element, cfgs=list(cfg2resp.keys()), **kwargs
    )
    # Now go deeper and split based on the best-distinguishing element.
    true_cfgs = {
        mult: elements
        for mult, elements in cfg2resp.items()
        if best_distinguishing_element in elements
    }
    true_child = build_distinguishing_tree(true_cfgs, oracle_response=True)
    true_child.parent = result
    false_cfgs = {
        mult: elements
        for mult, elements in cfg2resp.items()
        if best_distinguishing_element not in elements
    }
    false_child = build_distinguishing_tree(false_cfgs, oracle_response=False)
    false_child.parent = result
    return result
