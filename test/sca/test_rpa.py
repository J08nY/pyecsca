from unittest import TestCase

from parameterized import parameterized

from pyecsca.ec.context import local
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.params import get_params
from pyecsca.sca.re.rpa import MultipleContext


class MultipleContextTests(TestCase):

    @parameterized.expand([
        ("10", 10),
        ("2355498743", 2355498743),
        ("325385790209017329644351321912443757746", 325385790209017329644351321912443757746),
        ("13613624287328732", 13613624287328732)
    ])
    def test_basic(self, name, scalar):
        secp128r1 = get_params("secg", "secp128r1", "projective")
        base = secp128r1.generator
        coords = secp128r1.curve.coordinate_model
        add = coords.formulas["add-1998-cmo"]
        dbl = coords.formulas["dbl-1998-cmo"]
        scl = coords.formulas["z"]
        mult = LTRMultiplier(add, dbl, scl, always=False, complete=False, short_circuit=True)
        with local(MultipleContext()) as ctx:
            mult.init(secp128r1, base)
            mult.multiply(scalar)
        muls = list(ctx.points.values())
        self.assertEqual(muls[-1], scalar)
