from pyecsca.ec.params import get_params
from importlib_resources import as_file
from pyecsca.ec.formula import (
    AdditionFormula,
    LadderFormula,
    DoublingFormula,
    AdditionEFDFormula,
    DoublingEFDFormula,
    LadderEFDFormula,
)

from pathlib import Path
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel, TwistedEdwardsModel
from pyecsca.ec.formula_gen.fliparoo import generate_fliparood_formulas
from pyecsca.ec.formula_gen.switch_sign import generate_switched_formulas
from pyecsca.ec.formula_gen.partitions import (
    reduce_all_adds,
    expand_all_muls,
    expand_all_nopower2_muls,
)
from pyecsca.ec.formula_gen.formula_graph import rename_ivs


def main():
    for name, lib_formula in load_library_formulas().items():
        print(name)
        test_formula_graph(lib_formula, library=True)
        test_formula(lib_formula, library=True)
        test_fliparood_formula(lib_formula, library=True)
        test_switch_sign(lib_formula, library=True)
        test_reductions(lib_formula, library=True)
        test_expansions(lib_formula, library=True)
    for name, formula in load_efd_formulas(
        "projective", ShortWeierstrassModel()
    ).items():
        print(name)
        test_fliparood_formula(formula)
        test_switch_sign(formula)
        test_reductions(formula)
        test_expansions(formula)
    print("All good.")


def test_formula_graph(formula, library=False):
    test_formula(rename_ivs(formula), library)


def test_switch_sign(formula, library=False):
    for switch_formula in generate_switched_formulas(formula):
        test_formula(switch_formula, library)


def test_fliparood_formula(formula, library=False):
    for fliparood in generate_fliparood_formulas(formula):
        test_formula(fliparood, library)


def test_reductions(formula, library=False):
    test_formula(reduce_all_adds(formula), library)


def test_expansions(formula, library=False):
    test_formula(expand_all_muls(formula), library)
    test_formula(expand_all_nopower2_muls(formula), library)


def test_formula(formula, library=False):
    try:
        test_formula0(formula, library)
    except AssertionError:
        print(formula.name)


def test_formula0(formula, library=False):
    coordinate_model = formula.coordinate_model
    param_spec = choose_curve(coordinate_model, formula.name, library)
    params = get_params(*param_spec, coordinate_model.name)
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


def load_efd_formulas(coordinate_name, model):
    formulas = model.coordinates[coordinate_name].formulas
    return {name: f for name, f in formulas.items() if "add" in name or "dbl" in name}


def load_library_formulas(coordinates=None):
    libs_dict = {}
    for name, model, coords, _, formula_type in LIBRARY_FORMULAS:
        if coordinates is not None and coordinates != coords:
            continue
        coordinate_model = model().coordinates[coords]
        lib_path = Path("test/data/formulas")  # Path("../../../test/data/formulas")
        with as_file(lib_path.joinpath(name)) as meta_path, as_file(
            lib_path.joinpath(name + ".op3")
        ) as op3_path:
            libs_dict[name] = formula_type(meta_path, op3_path, name, coordinate_model)
    return libs_dict


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
]


def choose_curve(coordinate_model, name, library):
    if library:
        return next(filter(lambda x: x[0] == name, LIBRARY_FORMULAS))[3]
    model = coordinate_model.curve_model
    if model.__class__ == ShortWeierstrassModel:
        return ("secg", "secp128r1")
    if model.__class__ == MontgomeryModel:
        return ("other", "Curve25519")
    if model.__class__ == TwistedEdwardsModel:
        return ("other", "Ed25519")
    raise NotImplementedError(model)


if __name__ == "__main__":
    main()
