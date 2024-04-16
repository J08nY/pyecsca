import pickle
from operator import itemgetter
from typing import Tuple

import pytest
from sympy import FF, symbols
from importlib_resources import files, as_file
import test.data.formulas
from pyecsca.ec.formula.expand import expand_formula_set
from pyecsca.ec.formula.fliparoo import generate_fliparood_formulas
from pyecsca.ec.formula.graph import rename_ivs
from pyecsca.ec.formula.metrics import (
    formula_similarity,
    formula_similarity_abs,
    formula_similarity_fuzz,
)
from pyecsca.ec.formula.partitions import (
    reduce_all_adds,
    expand_all_muls,
    expand_all_nopower2_muls,
    generate_partitioned_formulas,
)
from pyecsca.ec.formula.switch_sign import generate_switched_formulas
from pyecsca.ec.mod import SymbolicMod, Mod
from pyecsca.misc.cfg import TemporaryConfig
from pyecsca.ec.error import UnsatisfiedAssumptionError
from pyecsca.ec.params import get_params, DomainParameters
from pyecsca.ec.point import Point
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel, TwistedEdwardsModel
from pyecsca.ec.formula.efd import (
    AdditionEFDFormula,
    DoublingEFDFormula,
    LadderEFDFormula,
)
from pyecsca.ec.formula import (
    AdditionFormula,
    DoublingFormula,
    LadderFormula,
    CodeFormula,
)


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
    assert add.__eq__(add)
    assert add != dbl


def test_hashable(add):
    assert hash(add)


def test_num_ops(add):
    assert add.num_operations == 33
    assert add.num_multiplications == 17
    assert add.num_divisions == 0
    assert add.num_inversions == 0
    assert add.num_powers == 0
    assert add.num_squarings == 6
    assert add.num_addsubs == 10


def test_assumptions(secp128r1, mdbl):
    res = mdbl(secp128r1.curve.prime, secp128r1.generator, **secp128r1.curve.parameters)
    assert res is not None

    coords = {name: value * 5 for name, value in secp128r1.generator.coords.items()}
    other = Point(secp128r1.generator.coordinate_model, **coords)
    with pytest.raises(UnsatisfiedAssumptionError):
        mdbl(secp128r1.curve.prime, other, **secp128r1.curve.parameters)
    with TemporaryConfig() as cfg:
        cfg.ec.unsatisfied_formula_assumption_action = "ignore"
        pt = mdbl(secp128r1.curve.prime, other, **secp128r1.curve.parameters)
        assert pt is not None


def test_parameters():
    jac_secp128r1 = get_params("secg", "secp128r1", "jacobian")
    jac_dbl = jac_secp128r1.curve.coordinate_model.formulas["dbl-1998-hnm"]

    res = jac_dbl(
        jac_secp128r1.curve.prime,
        jac_secp128r1.generator,
        **jac_secp128r1.curve.parameters,
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
    generator_double = dbl(p, secp128r1.generator, **secp128r1.curve.parameters)[0]
    for outer_var in coords.variables:
        symbolic_val = getattr(symbolic_double, outer_var).x
        generator_val = getattr(generator_double, outer_var).x
        for inner_var in coords.variables:
            symbolic_val = symbolic_val.subs(
                inner_var, k(getattr(secp128r1.generator, inner_var).x)
            )
        assert Mod(int(symbolic_val), p) == Mod(generator_val, p)


def test_pickle(add, dbl):
    assert add == pickle.loads(pickle.dumps(add))


def test_compare(add, dbl):
    assert add < dbl


def test_formula_similarity(secp128r1):
    add_bl = secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
    add_rcb = secp128r1.curve.coordinate_model.formulas["add-2015-rcb"]
    out = formula_similarity(add_bl, add_rcb)
    assert out["output"] == 0
    assert out["ivs"] < 0.5
    out_abs = formula_similarity_abs(add_bl, add_rcb)
    assert out_abs["output"] == 0
    assert out_abs["ivs"] < 0.5
    out_fuzz = formula_similarity_fuzz(add_bl, add_rcb, secp128r1.curve, samples=100)
    assert out_fuzz["output"] == 0
    assert out_fuzz["ivs"] < 0.5
    out_same = formula_similarity(add_bl, add_bl)
    assert out_same["output"] == 1
    assert out_same["ivs"] == 1


LIBRARY_FORMULAS = [
    [
        "add-bc-r1rv76-jac",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp128r1"),
        AdditionEFDFormula,
    ],
    [
        "add-bc-r1rv76-mod",
        ShortWeierstrassModel,
        "modified",
        ("secg", "secp128r1"),
        AdditionEFDFormula,
    ],
    [
        "dbl-bc-r1rv76-jac",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp128r1"),
        DoublingEFDFormula,
    ],
    [
        "dbl-bc-r1rv76-mod",
        ShortWeierstrassModel,
        "modified",
        ("secg", "secp128r1"),
        DoublingEFDFormula,
    ],
    [
        "dbl-bc-r1rv76-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        DoublingEFDFormula,
    ],
    [
        "ladd-bc-r1rv76-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        LadderEFDFormula,
    ],
    [
        "dbl-boringssl-p224",
        ShortWeierstrassModel,
        "jacobian-3",
        ("secg", "secp224r1"),
        DoublingEFDFormula,
    ],
    [
        "add-boringssl-p224",
        ShortWeierstrassModel,
        "jacobian-3",
        ("secg", "secp224r1"),
        AdditionEFDFormula,
    ],
    [
        "add-libressl-v382",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp128r1"),
        AdditionEFDFormula,
    ],
    [
        "dbl-libressl-v382",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp128r1"),
        DoublingEFDFormula,
    ],
    [
        "madd-secp256k1-v040",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp256k1"),
        AdditionEFDFormula,
    ],
    [
        "dbl-secp256k1-v040",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp256k1"),
        DoublingEFDFormula,
    ],
    [
        "add-openssl-z256",
        ShortWeierstrassModel,
        "jacobian-3",
        ("secg", "secp256r1"),
        AdditionEFDFormula,
    ],
    [
        "add-openssl-z256a",
        ShortWeierstrassModel,
        "jacobian-3",
        ("secg", "secp256r1"),
        AdditionEFDFormula,
    ],
    [
        "ladd-openssl-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        LadderEFDFormula,
    ],
    [
        "ladd-hacl-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        LadderEFDFormula,
    ],
    [
        "dbl-hacl-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        DoublingEFDFormula,
    ],
    [
        "dbl-sunec-v21",
        ShortWeierstrassModel,
        "projective-3",
        ("secg", "secp256r1"),
        DoublingEFDFormula,
    ],
    [
        "add-sunec-v21",
        ShortWeierstrassModel,
        "projective-3",
        ("secg", "secp256r1"),
        AdditionEFDFormula,
    ],
    [
        "add-sunec-v21-ed25519",
        TwistedEdwardsModel,
        "extended",
        ("other", "Ed25519"),
        AdditionEFDFormula,
    ],
    [
        "dbl-sunec-v21-ed25519",
        TwistedEdwardsModel,
        "extended",
        ("other", "Ed25519"),
        DoublingEFDFormula,
    ],
    [
        "ladd-rfc7748",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        LadderEFDFormula,
    ],
    [
        "add-bearssl-v06",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp256r1"),
        AdditionEFDFormula,
    ],
    [
        "dbl-bearssl-v06",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp256r1"),
        DoublingEFDFormula,
    ],
    [
        "add-libgcrypt-v1102",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp256r1"),
        AdditionEFDFormula,
    ],
    [
        "dbl-libgcrypt-v1102",
        ShortWeierstrassModel,
        "jacobian",
        ("secg", "secp256r1"),
        DoublingEFDFormula,
    ],
    [
        "ladd-go-1214",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        LadderEFDFormula,
    ],
    [
        "add-gecc-322",
        ShortWeierstrassModel,
        "jacobian-3",
        ("secg", "secp256r1"),
        AdditionEFDFormula,
    ],
    [
        "dbl-gecc-321",
        ShortWeierstrassModel,
        "jacobian-3",
        ("secg", "secp256r1"),
        DoublingEFDFormula,
    ],
    [
        "ladd-boringssl-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        LadderEFDFormula,
    ],
    [
        "dbl-ipp-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        DoublingEFDFormula,
    ],
    [
        "ladd-botan-x25519",
        MontgomeryModel,
        "xz",
        ("other", "Curve25519"),
        LadderEFDFormula,
    ],
]


@pytest.fixture(params=LIBRARY_FORMULAS, ids=list(map(itemgetter(0), LIBRARY_FORMULAS)))
def library_formula_params(request) -> Tuple[CodeFormula, DomainParameters]:
    name, model, coords_name, param_spec, formula_type = request.param
    model = model()
    coordinate_model = model.coordinates[coords_name]
    with as_file(files(test.data.formulas).joinpath(name)) as meta_path, as_file(
        files(test.data.formulas).joinpath(name + ".op3")
    ) as op3_path:
        formula = formula_type(meta_path, op3_path, name, coordinate_model).to_code()
    params = get_params(*param_spec, coords_name)
    return formula, params


def test_formula_graph(library_formula_params):
    formula, params = library_formula_params
    renamed = rename_ivs(formula)
    do_test_formula(renamed, params)
    assert hash(renamed)


def test_switch_sign(library_formula_params):
    formula, params = library_formula_params
    for switch_formula in generate_switched_formulas(formula):
        do_test_formula(switch_formula, params)


def test_fliparood_formula(library_formula_params):
    formula, params = library_formula_params
    for fliparood in generate_fliparood_formulas(formula):
        do_test_formula(fliparood, params)


def test_partition_formula_single(library_formula_params):
    formula, params = library_formula_params
    try:
        next(iter(generate_partitioned_formulas(formula)))
    except StopIteration:
        pass


@pytest.mark.slow
def test_partition_formula(library_formula_params):
    formula, params = library_formula_params
    for partitioned in generate_partitioned_formulas(formula):
        do_test_formula(partitioned, params)


def test_reductions(library_formula_params):
    formula, params = library_formula_params
    do_test_formula(reduce_all_adds(formula), params)


def test_expansions(library_formula_params):
    formula, params = library_formula_params
    do_test_formula(expand_all_muls(formula), params)
    do_test_formula(expand_all_nopower2_muls(formula), params)


def do_test_formula(formula, params):
    coordinate_model = formula.coordinate_model
    scale = coordinate_model.formulas.get("z", None)
    if scale is None:
        scale = coordinate_model.formulas.get("scale", None)

    formula_type = formula.__class__
    for _ in range(10):
        Paff = params.curve.affine_random()
        P2aff = params.curve.affine_double(Paff)
        Qaff = params.curve.affine_random()
        Q2aff = params.curve.affine_double(Qaff)
        Raff = params.curve.affine_add(Paff, Qaff)
        R2aff = params.curve.affine_double(Raff)
        QRaff = params.curve.affine_add(Qaff, Raff)
        P = Paff.to_model(coordinate_model, params.curve)
        P2 = P2aff.to_model(coordinate_model, params.curve)
        Q = Qaff.to_model(coordinate_model, params.curve)
        Q2 = Q2aff.to_model(coordinate_model, params.curve)
        R = Raff.to_model(coordinate_model, params.curve)
        R2 = R2aff.to_model(coordinate_model, params.curve)  # noqa
        QR = QRaff.to_model(coordinate_model, params.curve)
        inputs = (P, Q, R)[: formula.num_inputs]
        res = formula(params.curve.prime, *inputs, **params.curve.parameters)
        if issubclass(formula_type, AdditionFormula):
            try:
                assert res[0].to_affine() == Raff
            except NotImplementedError:
                assert (
                    scale(params.curve.prime, res[0], **params.curve.parameters)[0] == R
                )
        elif issubclass(formula_type, DoublingFormula):
            try:
                assert res[0].to_affine() == P2aff
            except NotImplementedError:
                assert (
                    scale(params.curve.prime, res[0], **params.curve.parameters)[0]
                    == P2
                )
        elif issubclass(formula_type, LadderFormula):
            try:
                assert res[0].to_affine() == Q2aff
                assert res[1].to_affine() == QRaff
            except NotImplementedError:
                # print(scale(params.curve.prime, res[0], **params.curve.parameters)[0])
                # print(scale(params.curve.prime, res[1], **params.curve.parameters)[0])
                # print(P)
                # print(Q)
                # print(R)
                # print(P2)
                # print(Q2)
                # print(R2)
                # print(QR)
                # print("------------------------------------")
                assert (
                    scale(params.curve.prime, res[1], **params.curve.parameters)[0]
                    == QR
                )
                assert (
                    scale(params.curve.prime, res[0], **params.curve.parameters)[0]
                    == Q2
                )


def test_formula_correctness(library_formula_params):
    formula, params = library_formula_params
    do_test_formula(formula, params)


def test_formula_expand(add):
    res = expand_formula_set({add})
    assert len(res) > 1
