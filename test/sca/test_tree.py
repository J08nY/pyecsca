import io
from contextlib import redirect_stdout

from pyecsca.sca.re.tree import Tree, Map
import pandas as pd


def test_build_tree():
    cfgs = ["a", "b", "c"]
    inputs1 = [1, 2, 3, 4]
    codomain1 = {0, 1, 3, 4, 5}
    mapping1 = pd.DataFrame([(0, 4, 5, 0), (0, 3, 0, 0), (1, 4, 0, 0)], columns=inputs1, index=cfgs)
    dmap1 = Map(mapping1, codomain1)

    inputs2 = ["f", "e", "d"]
    codomain2 = {0, 1, 2, 3}
    mapping2 = pd.DataFrame([(1, 0, 0), (2, 0, 0), (3, 0, 0)], columns=inputs2, index=cfgs)
    dmap2 = Map(mapping2, codomain2)
    tree = Tree.build(set(cfgs), dmap1, dmap2)
    with redirect_stdout(io.StringIO()):
        tree.render()
        tree.describe()


def test_expand_tree():
    cfgs = ["a", "b", "c"]
    inputs1 = [1, 2]
    codomain1 = {0, 3, 4}
    mapping1 = pd.DataFrame([(0, 4), (0, 3), (0, 4)], columns=inputs1, index=cfgs)
    dmap1 = Map(mapping1, codomain1)

    inputs2 = ["f", "e", "d"]
    codomain2 = {0, 1, 2, 3}
    mapping2 = pd.DataFrame([(1, 0, 0), (2, 0, 0), (3, 0, 0)], columns=inputs2, index=cfgs)
    dmap2 = Map(mapping2, codomain2)
    tree = Tree.build(set(cfgs), dmap1)
    res = tree.expand(dmap2)
    assert res.height > tree.height
