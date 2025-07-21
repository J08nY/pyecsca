from functools import partial

from pyecsca.ec.countermeasures import BrumleyTuveri
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.params import get_params
from pyecsca.sca.re.rpa import multiples_computed


def test_multiples_computed():
    params = get_params("secg", "secp256r1", "projective")
    scalar = (
        178351107805817428630633067540716126328949183057477388943177779766598408516705
    )
    mult_class = LTRMultiplier
    mult_factory = partial(LTRMultiplier, always=False, complete=True)
    full_factory = lambda *args, **kwargs: BrumleyTuveri(mult_factory(*args, **kwargs))  # noqa: E731
    r = multiples_computed(scalar, params, mult_class, full_factory)
    assert r
