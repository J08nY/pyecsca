import pytest

from pyecsca.ec.mult import LTRMultiplier
from pyecsca.sca.attack.DPA import DPA
from pyecsca.sca.attack.CPA import CPA
from pyecsca.sca.target import LeakageTarget
from pyecsca.sca.attack import HammingWeight


@pytest.fixture()
def mult(secp128r1):
    return LTRMultiplier(
        secp128r1.curve.coordinate_model.formulas["add-2015-rcb"],
        secp128r1.curve.coordinate_model.formulas["dbl-2015-rcb"],
    )


@pytest.fixture()
def target(secp128r1, mult):
    target = LeakageTarget(
        secp128r1.curve.model, secp128r1.curve.coordinate_model, mult, HammingWeight()
    )
    target.set_params(secp128r1)
    return target


@pytest.mark.xfail(reason="May fail intermittently.")
def test_dpa(secp128r1, mult, target):
    scalar = 5
    pub = secp128r1.curve.affine_multiply(
        secp128r1.generator.to_affine(), scalar
    ).to_model(secp128r1.curve.coordinate_model, secp128r1.curve)
    points, traces = target.simulate_scalar_mult_traces(700, scalar)
    dpa = DPA(points, traces, mult, secp128r1)
    res = dpa.perform(3, pub)
    assert res == 5


@pytest.mark.xfail(reason="May fail intermittently.")
def test_cpa(secp128r1, mult, target):
    scalar = 5
    pub = secp128r1.curve.affine_multiply(
        secp128r1.generator.to_affine(), scalar
    ).to_model(secp128r1.curve.coordinate_model, secp128r1.curve)
    points, traces = target.simulate_scalar_mult_traces(100, scalar)
    cpa = CPA(points, traces, HammingWeight(), mult, secp128r1)
    res = cpa.perform(3, pub)
    assert res == 5