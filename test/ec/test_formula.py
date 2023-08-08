import pytest
from sympy import FF, symbols

from pyecsca.ec.mod import SymbolicMod, Mod
from pyecsca.misc.cfg import TemporaryConfig
from pyecsca.ec.error import UnsatisfiedAssumptionError
from pyecsca.ec.params import get_params
from pyecsca.ec.point import Point


@pytest.fixture()
def add(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["add-2007-bl"]


@pytest.fixture()
def dbl(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["dbl-2007-bl"]


@pytest.fixture()
def mdbl(secp128r1):
    return secp128r1.curve.coordinate_model.formulas["mdbl-2007-bl"]


def test_wrong_call(secp128r1, add):
    with pytest.raises(ValueError):
        add(secp128r1.curve.prime)
    with pytest.raises(ValueError):
        add(
            secp128r1.curve.prime,
            secp128r1.generator.to_affine(),
            secp128r1.generator.to_affine(),
        )


def test_indices(add):
    assert add.input_index == 1
    assert add.output_index == 3


def test_inputs_outputs(add):
    assert add.inputs == {"X1", "Y1", "Z1", "X2", "Y2", "Z2"}
    assert add.outputs == {"X3", "Y3", "Z3"}


def test_eq(add, dbl):
    assert add == add
    assert add != dbl


def test_num_ops(add):
    assert add.num_operations == 33
    assert add.num_multiplications == 17
    assert add.num_divisions == 0
    assert add.num_inversions == 0
    assert add.num_powers == 0
    assert add.num_squarings == 6
    assert add.num_addsubs == 10


def test_assumptions(secp128r1, mdbl):
    res = mdbl(
        secp128r1.curve.prime,
        secp128r1.generator,
        **secp128r1.curve.parameters
    )
    assert res is not None

    coords = {
        name: value * 5 for name, value in secp128r1.generator.coords.items()
    }
    other = Point(secp128r1.generator.coordinate_model, **coords)
    with pytest.raises(UnsatisfiedAssumptionError):
        mdbl(
            secp128r1.curve.prime, other, **secp128r1.curve.parameters
        )
    with TemporaryConfig() as cfg:
        cfg.ec.unsatisfied_formula_assumption_action = "ignore"
        pt = mdbl(
            secp128r1.curve.prime, other, **secp128r1.curve.parameters
        )
        assert pt is not None


def test_parameters():
    jac_secp128r1 = get_params("secg", "secp128r1", "jacobian")
    jac_dbl = jac_secp128r1.curve.coordinate_model.formulas[
        "dbl-1998-hnm"
    ]

    res = jac_dbl(
        jac_secp128r1.curve.prime,
        jac_secp128r1.generator,
        **jac_secp128r1.curve.parameters
    )
    assert res is not None


def test_symbolic(secp128r1, dbl):
    p = secp128r1.curve.prime
    k = FF(p)
    coords = secp128r1.curve.coordinate_model
    sympy_params = {
        key: SymbolicMod(k(int(value)), p)
        for key, value in secp128r1.curve.parameters.items()
    }
    symbolic_point = Point(
        coords, **{key: SymbolicMod(symbols(key), p) for key in coords.variables}
    )
    symbolic_double = dbl(p, symbolic_point, **sympy_params)[0]
    generator_double = dbl(
        p, secp128r1.generator, **secp128r1.curve.parameters
    )[0]
    for outer_var in coords.variables:
        symbolic_val = getattr(symbolic_double, outer_var).x
        generator_val = getattr(generator_double, outer_var).x
        for inner_var in coords.variables:
            symbolic_val = symbolic_val.subs(
                inner_var, k(getattr(secp128r1.generator, inner_var).x)
            )
        assert Mod(int(symbolic_val), p) == Mod(generator_val, p)
