from unittest import TestCase

from pyecsca.ec.naf import naf, wnaf


class NafTests(TestCase):
    def test_nafs(self):
        i = 0b1100110101001101011011
        self.assertListEqual(naf(i), wnaf(i, 2))
