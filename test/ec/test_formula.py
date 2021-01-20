from unittest import TestCase

from sympy import FF, symbols

from pyecsca.ec.mod import SymbolicMod, Mod
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
            self.add(self.secp128r1.curve.prime)
        with self.assertRaises(ValueError):
            self.add(self.secp128r1.curve.prime, self.secp128r1.generator.to_affine(), self.secp128r1.generator.to_affine())

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
        res = self.mdbl(self.secp128r1.curve.prime, self.secp128r1.generator, **self.secp128r1.curve.parameters)
        self.assertIsNotNone(res)

        coords = {name: value * 5 for name, value in self.secp128r1.generator.coords.items()}
        other = Point(self.secp128r1.generator.coordinate_model, **coords)
        with self.assertRaises(UnsatisfiedAssumptionError):
            self.mdbl(self.secp128r1.curve.prime, other, **self.secp128r1.curve.parameters)
        with TemporaryConfig() as cfg:
            cfg.ec.unsatisfied_formula_assumption_action = "ignore"
            pt = self.mdbl(self.secp128r1.curve.prime, other, **self.secp128r1.curve.parameters)
            self.assertIsNotNone(pt)

    def test_parameters(self):
        res = self.jac_dbl(self.secp128r1.curve.prime, self.jac_secp128r1.generator, **self.jac_secp128r1.curve.parameters)
        self.assertIsNotNone(res)

    def test_symbolic(self):
        p = self.secp128r1.curve.prime
        k = FF(p)
        coords = self.secp128r1.curve.coordinate_model
        sympy_params = {key: SymbolicMod(k(int(value)), p) for key, value in self.secp128r1.curve.parameters.items()}
        symbolic_point = Point(coords, **{key: SymbolicMod(symbols(key), p) for key in coords.variables})
        symbolic_double = self.dbl(p, symbolic_point, **sympy_params)[0]
        generator_double = self.dbl(p, self.secp128r1.generator, **self.secp128r1.curve.parameters)[0]
        for outer_var in coords.variables:
            symbolic_val = getattr(symbolic_double, outer_var).x
            generator_val = getattr(generator_double, outer_var).x
            for inner_var in coords.variables:
                symbolic_val = symbolic_val.subs(inner_var, k(getattr(self.secp128r1.generator, inner_var).x))
            self.assertEqual(Mod(int(symbolic_val), p), Mod(generator_val, p))
