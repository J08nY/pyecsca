from importlib_resources import files, as_file
import test.data.formulas
from pyecsca.ec.formula import AdditionEFDFormula
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.params import get_params
from pyecsca.sca.re.structural import formula_similarity, formula_similarity_fuzz


def test_formula_match():
    model = ShortWeierstrassModel()
    coords = model.coordinates["jacobian"]
    secp128r1 = get_params("secg", "secp128r1", "jacobian")
    with as_file(
        files(test.data.formulas).joinpath("add-bc-r1rv76")
    ) as meta_path, as_file(
        files(test.data.formulas).joinpath("add-bc-r1rv76.op3")
    ) as op3_path:
        bc_formula = AdditionEFDFormula(meta_path, op3_path, "add-bc-r1rv76", coords)
    print()
    for other_name, other_formula in coords.formulas.items():
        if not other_name.startswith("add"):
            continue
        print(other_name, "fuzz", formula_similarity_fuzz(other_formula, bc_formula, secp128r1.curve, 1000), "symbolic", formula_similarity(other_formula, bc_formula))


def test_efd_formula_match():
    model = ShortWeierstrassModel()
    coords = model.coordinates["modified"]
    print()
    for other_name, other_formula in coords.formulas.items():
        if not other_name.startswith("add"):
            continue
        for one_name, one_formula in coords.formulas.items():
            if not one_name.startswith("add"):
                continue
            print(one_name, other_name, formula_similarity(one_formula, other_formula))
