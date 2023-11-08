import pytest
from importlib_resources import files, as_file
import test.data.formulas
from pyecsca.ec.formula import (
    AdditionEFDFormula,
    LadderEFDFormula,
    DoublingEFDFormula,
    AdditionFormula,
    DoublingFormula,
    LadderFormula,
)
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel
from pyecsca.ec.params import get_params
from pyecsca.sca.re.structural import formula_similarity, formula_similarity_fuzz
import itertools


def test_formula_match():
    model = ShortWeierstrassModel()
    coords = model.coordinates["jacobian"]
    secp128r1 = get_params("secg", "secp224r1", "jacobian-3")
    with as_file(
        files(test.data.formulas).joinpath("dbl-boringssl-p224")
    ) as meta_path, as_file(
        files(test.data.formulas).joinpath("dbl-boringssl-p224.op3")
    ) as op3_path:
        bc_formula = DoublingEFDFormula(
            meta_path, op3_path, "dbl-boringssl-p224", coords
        )
    print()
    for other_name, other_formula in coords.formulas.items():
        if not other_name.startswith("dbl"):
            continue
        print(
            other_name,
            "fuzz",
            formula_similarity_fuzz(other_formula, bc_formula, secp128r1.curve, 1000),
            "symbolic",
            formula_similarity(other_formula, bc_formula),
        )


def test_formula_match1():
    model = MontgomeryModel()
    coords = model.coordinates["xz"]
    curve25519 = get_params("other", "Curve25519", "xz")
    with as_file(
        files(test.data.formulas).joinpath("dbl-bc-r1rv76-x25519")
    ) as meta_path, as_file(
        files(test.data.formulas).joinpath("dbl-bc-r1rv76-x25519.op3")
    ) as op3_path:
        bc_formula = DoublingEFDFormula(
            meta_path, op3_path, "dbl-bc-r1rv76-x25519", coords
        )
    print()
    for other_name, other_formula in coords.formulas.items():
        if not other_name.startswith("dbl"):
            continue
        print(
            other_name,
            "fuzz",
            formula_similarity_fuzz(other_formula, bc_formula, curve25519.curve, 1000),
            "symbolic",
            formula_similarity(other_formula, bc_formula),
        )


def test_efd_formula_match():
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    secp128r1 = get_params("secg", "secp128r1", "projective")
    print()
    adds = list(filter(lambda tup: tup[0].startswith("add"), coords.formulas.items()))
    for one, other in itertools.combinations_with_replacement(adds, 2):
        one_name, one_formula = one
        other_name, other_formula = other
        print(
            one_name,
            other_name,
            "fuzz",
            formula_similarity_fuzz(one_formula, other_formula, secp128r1.curve, 1000),
            "symbolic",
            formula_similarity(one_formula, other_formula),
        )


@pytest.mark.parametrize(
    "name,model,coords,param_spec,formula_type",
    [
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
            "dbl-secp256k1-v040",
            ShortWeierstrassModel,
            "jacobian",
            ("secg", "secp256k1"),
            DoublingEFDFormula,
        ],
    ],
)
def test_formula_correctness(name, model, coords, param_spec, formula_type):
    model = model()
    coordinate_model = model.coordinates[coords]
    with as_file(files(test.data.formulas).joinpath(name)) as meta_path, as_file(
        files(test.data.formulas).joinpath(name + ".op3")
    ) as op3_path:
        formula = formula_type(meta_path, op3_path, name, coordinate_model)
    params = get_params(*param_spec, coords)
    scale = coordinate_model.formulas.get("z", None)
    if scale is None:
        scale = coordinate_model.formulas.get("scale", None)
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
