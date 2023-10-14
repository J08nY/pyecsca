import pickle

from pyecsca.ec.model import (
    ShortWeierstrassModel,
    MontgomeryModel,
    EdwardsModel,
    TwistedEdwardsModel,
)


def test_load():
    assert len(ShortWeierstrassModel().coordinates) > 0
    assert len(MontgomeryModel().coordinates) > 0
    assert len(EdwardsModel().coordinates) > 0
    assert len(TwistedEdwardsModel().coordinates) > 0


def test_pickle():
    sw = ShortWeierstrassModel()
    m = MontgomeryModel()
    e = EdwardsModel()
    te = TwistedEdwardsModel()
    assert sw == pickle.loads(pickle.dumps(sw))
    assert m == pickle.loads(pickle.dumps(MontgomeryModel()))
    assert e == pickle.loads(pickle.dumps(EdwardsModel()))
    assert te == pickle.loads(pickle.dumps(TwistedEdwardsModel()))
