from unittest import TestCase

from pyecsca.misc.cfg import TemporaryConfig
from pyecsca.ec.error import UnsatisfiedAssumptionError
from pyecsca.ec.params import get_params
from pyecsca.ec.point import Point


class FormulaTests(TestCase):

    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.add = self.secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
        self.dbl = self.secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]
        self.mdbl = self.secp128r1.curve.coordinate_model.formulas["mdbl-2007-bl"]
        self.jac_secp128r1 = get_params("secg", "secp128r1", "jacobian")
        self.jac_dbl = self.jac_secp128r1.curve.coordinate_model.formulas["dbl-1998-hnm"]

    def test_wrong_call(self):
        with self.assertRaises(ValueError):
            self.add()
        with self.assertRaises(ValueError):
            self.add(self.secp128r1.generator.to_affine(), self.secp128r1.generator.to_affine())

    def test_indices(self):
        self.assertEqual(self.add.input_index, 1)
        self.assertEqual(self.add.output_index, 3)

    def test_inputs_outputs(self):
        self.assertEqual(self.add.inputs, {"X1", "Y1", "Z1", "X2", "Y2", "Z2"})
        self.assertEqual(self.add.outputs, {"X3", "Y3", "Z3"})

    def test_eq(self):
        self.assertEqual(self.add, self.add)
        self.assertNotEqual(self.add, self.dbl)

    def test_num_ops(self):
        self.assertEqual(self.add.num_operations, 33)
        self.assertEqual(self.add.num_multiplications, 17)
        self.assertEqual(self.add.num_divisions, 0)
        self.assertEqual(self.add.num_inversions, 0)
        self.assertEqual(self.add.num_powers, 0)
        self.assertEqual(self.add.num_squarings, 6)
        self.assertEqual(self.add.num_addsubs, 10)

    def test_assumptions(self):
        res = self.mdbl(self.secp128r1.generator, **self.secp128r1.curve.parameters)
        self.assertIsNotNone(res)

        coords = {name: value * 5 for name, value in self.secp128r1.generator.coords.items()}
        other = Point(self.secp128r1.generator.coordinate_model, **coords)
        with self.assertRaises(UnsatisfiedAssumptionError):
            self.mdbl(other, **self.secp128r1.curve.parameters)
        with TemporaryConfig() as cfg:
            cfg.ec.unsatisfied_formula_assumption_action = "ignore"
            pt = self.mdbl(other, **self.secp128r1.curve.parameters)
            self.assertIsNotNone(pt)

    def test_parameters(self):
        res = self.jac_dbl(self.jac_secp128r1.generator, **self.jac_secp128r1.curve.parameters)
        self.assertIsNotNone(res)
