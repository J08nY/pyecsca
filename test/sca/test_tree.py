import random
import time

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

    io_map = {"a": {1: 5, 2: 7}, "b": {1: 3}}
    dmap = Map.from_io_maps(cfgs, io_map)
    assert dmap.domain == [1, 2]
    assert dmap.codomain == {5, 3, 7, None}


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
    tree.describe()


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
    index = list(range(nrows))
    df = pd.DataFrame(
        [random.choices((True, False), k=ncols) for _ in index], index=index
    )
    print(df.memory_usage().sum())
    start = time.perf_counter()
    for row, data in df.groupby(df.columns.tolist(), as_index=False):
        pass
    end = time.perf_counter()
    print(end - start)
