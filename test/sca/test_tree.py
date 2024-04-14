import random
from collections import OrderedDict
from copy import deepcopy

from pyecsca.sca.re.tree import Tree, Map
import pandas as pd


def test_map():
    cfgs = {"a", "b"}
    binary_sets = {"a": {1, 2, 3}, "b": {2, 4}}
    dmap = Map.from_sets(cfgs, binary_sets)
    assert dmap.domain == [1, 2, 3, 4]
    assert dmap.codomain == {True, False}
    assert dmap.mapping.index.tolist() == [0, 1]
    assert set(dmap.cfg_map.index) == cfgs
    assert dmap.cfgs == cfgs
    assert dmap["a", 1]
    assert not dmap["a", 4]

    io_map = {"a": {1: 5, 2: 7}, "b": {1: 3}}
    dmap = Map.from_io_maps(cfgs, io_map)
    assert dmap.domain == [1, 2]
    assert dmap.codomain == {5, 3, 7, None}

    io_map_full = {"a": {1: 5, 2: 7}, "b": {1: 3, 2: 11}}
    dmap = Map.from_io_maps(cfgs, io_map_full)
    assert dmap.domain == [1, 2]
    assert dmap.codomain == {5, 3, 7, 11}


def test_map_merge():
    cfgs = {"a", "b"}
    binary_sets = {"a": {1, 2, 3}, "b": {2, 4}}
    dmap1 = Map.from_sets(cfgs, binary_sets)
    assert len(dmap1.mapping) == 2

    cfgs = {"c", "d"}
    binary_sets = {"c": {1, 2}, "d": {2, 4, 3}}
    dmap2 = Map.from_sets(cfgs, binary_sets)
    assert len(dmap2.mapping) == 2
    merged = deepcopy(dmap1)
    merged.merge(dmap2)
    assert len(merged.mapping) == 4
    assert len(merged.cfg_map) == 4
    assert len(merged.codomain) == 2
    for i in [1, 2, 3, 4]:
        for cfg in "ab":
            assert merged[cfg, i] == dmap1[cfg, i]
        for cfg in "cd":
            assert merged[cfg, i] == dmap2[cfg, i]


def test_map_deduplicate():
    cfgs = {"a", "b", "c", "d"}
    binary_sets = {"a": {1, 2, 3}, "b": {2, 3, 4}, "c": {1, 2, 3}, "d": {4, 2}}
    dmap = Map.from_sets(cfgs, binary_sets)
    original = deepcopy(dmap)
    dmap.deduplicate()
    for cfg in cfgs:
        for i in [1, 2, 3, 4]:
            assert dmap[cfg, i] == original[cfg, i]
    assert len(dmap.mapping) < len(original.mapping)
    assert dmap.cfgs == original.cfgs

    dedupped = Map.from_sets(cfgs, binary_sets, deduplicate=True)
    for cfg in cfgs:
        for i in [1, 2, 3, 4]:
            assert dedupped[cfg, i] == original[cfg, i]
    assert dedupped.cfgs == original.cfgs


def test_map_with_callable(secp128r1):
    add = secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
    dbl = secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
    mdbl = secp128r1.curve.coordinate_model.formulas["mdbl-2007-bl"]
    cfgs = [(add, dbl), (add, mdbl)]
    binary_sets = {cfgs[0]: {1, 2, 3}, cfgs[1]: {2, 3}}
    dmap = Map.from_sets(set(cfgs), binary_sets)
    assert dmap[cfgs[0], 1]


def test_build_tree():
    cfgs = ["a", "b", "c"]
    cfg_map = pd.DataFrame([0, 1, 2], index=cfgs, columns=["vals"])
    inputs1 = [1, 2, 3, 4]
    codomain1 = {0, 1, 3, 4, 5}
    mapping1 = pd.DataFrame([(0, 4, 5, 0), (0, 3, 0, 0), (1, 4, 0, 0)])
    dmap1 = Map(mapping1, cfg_map, inputs1, codomain1)

    inputs2 = ["f", "e", "d"]
    codomain2 = {0, 1, 2, 3}
    mapping2 = pd.DataFrame([(1, 0, 0), (2, 0, 0), (3, 0, 0)])
    dmap2 = Map(mapping2, cfg_map, inputs2, codomain2)
    tree = Tree.build(set(cfgs), dmap1, dmap2)
    tree.render()
    tree.render_basic()
    tree.describe()


def test_build_tree_dedup():
    """Make sure that dmap deduplication does not affect the tree."""
    cfgs = {"a", "b", "c", "d", "e", "f", "g"}
    binary_sets = {
        "a": {1, 2, 3},
        "b": {2, 3, 4},
        "c": {1, 2, 3},
        "d": {4, 2},
        "e": {4, 2},
        "f": {4, 2},
        "g": {4, 2},
    }
    dmap = Map.from_sets(cfgs, binary_sets)
    deduplicated = Map.from_sets(cfgs, binary_sets, deduplicate=True)
    original = deepcopy(dmap)
    dmap.deduplicate()

    tree = Tree.build(cfgs, original)
    dedup = Tree.build(cfgs, dmap)
    dedup_other = Tree.build(cfgs, deduplicated)
    print(tree.describe())
    assert tree.describe() == dedup.describe()
    assert tree.describe() == dedup_other.describe()


def test_build_tree_reorder():
    """Make sure that dmap input order does not affect the tree."""
    cfgs = {"a", "b", "c", "d", "e", "f", "g"}
    binary_sets = {
        "a": {1, 2, 3},
        "b": {2, 3, 4},
        "c": {1, 2, 3},
        "d": {4, 2},
        "e": {4, 2},
        "f": {4, 2},
        "g": {4, 2},
    }
    trees = set()
    for i in range(10):
        shuffled = list(binary_sets.items())
        random.shuffle(shuffled)
        bset = OrderedDict(shuffled)
        dmap = Map.from_sets(cfgs, bset)
        if i % 2 == 0:
            dmap.deduplicate()
        trees.add(Tree.build(cfgs, dmap).describe())
    assert len(trees) == 1


def test_expand_tree():
    cfgs = ["a", "b", "c"]
    cfg_map = pd.DataFrame([0, 1, 2], index=cfgs, columns=["vals"])
    inputs1 = [1, 2]
    codomain1 = {0, 3, 4}
    mapping1 = pd.DataFrame([(0, 4), (0, 3), (0, 4)])
    dmap1 = Map(mapping1, cfg_map, inputs1, codomain1)

    inputs2 = ["f", "e", "d"]
    codomain2 = {0, 1, 2, 3}
    mapping2 = pd.DataFrame([(1, 0, 0), (2, 0, 0), (3, 0, 0)])
    dmap2 = Map(mapping2, cfg_map, inputs2, codomain2)
    tree = Tree.build(set(cfgs), dmap1)
    res = tree.expand(dmap2)
    assert res.height > tree.height


def test_df():
    nrows = 12_000_000
    ncols = 5
    df = pd.DataFrame([random.choices((True, False), k=ncols) for _ in range(nrows)])
    cfg_map = pd.DataFrame(
        [(i,) for i in range(nrows)],
        index=[str(i) for i in range(nrows)],
        columns=["vals"],
    )
    dmap = Map(df, cfg_map, list(range(ncols)), {True, False})
    # start = time.perf_counter()
    dmap.deduplicate()
    # end = time.perf_counter()
