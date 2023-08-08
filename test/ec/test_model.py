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
