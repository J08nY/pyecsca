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
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel, TwistedEdwardsModel
from pyecsca.ec.params import get_params
from pyecsca.sca.re.structural import formula_similarity


def test_formula_similarity(secp128r1):
    add_bl = secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
    add_rcb = secp128r1.curve.coordinate_model.formulas["add-2015-rcb"]
    out = formula_similarity(add_bl, add_rcb)
    assert out["output"] == 0
    assert out["ivs"] < 0.5
    out_same = formula_similarity(add_bl, add_bl)
    assert out_same["output"] == 1
    assert out_same["ivs"] == 1


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
