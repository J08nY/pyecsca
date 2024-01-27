import pickle
import pickletools
from multiprocessing import get_context
from multiprocessing.context import BaseContext

import pytest

from pyecsca.ec.formula.efd import EFDFormula
from pyecsca.ec.formula.graph import FormulaGraph
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.params import get_params


@pytest.fixture()
def ctx() -> BaseContext:
    return get_context("spawn")


def model_target(obj):
    return obj._loaded


def test_model_loads(ctx):
    # Test that the unpickling of EFDCurveModel triggers a reload that loads the EFD data for that model.
    sw = ShortWeierstrassModel()
    with ctx.Pool(processes=1) as pool:
        res = pool.apply(model_target, args=(sw,))
        assert res


def test_model():
    sw = ShortWeierstrassModel()
    data = pickle.dumps(sw)
    back = pickle.loads(data)
    assert sw == back


def test_coords():
    sw = ShortWeierstrassModel()
    coords = sw.coordinates["projective"]
    data = pickle.dumps(coords)
    back = pickle.loads(data)
    assert coords == back


def test_formula():
    sw = ShortWeierstrassModel()
    coords = sw.coordinates["projective"]
    formula: EFDFormula = coords.formulas["add-2007-bl"]  # type: ignore
    data = pickle.dumps(formula)
    back = pickle.loads(data)
    assert formula == back
    formulas = tuple(coords.formulas.values())
    data = pickle.dumps(formulas)
    back = pickle.loads(data)
    assert formulas == back
    code_formula = formula.to_code()
    assert formula != code_formula
    back_code = pickle.loads(pickle.dumps(code_formula))
    assert code_formula == back_code


def formula_target(formula):
    return hasattr(formula, "coordinate_model")


def test_formula_loads(ctx):
    sw = ShortWeierstrassModel()
    coords = sw.coordinates["projective"]
    formula: EFDFormula = coords.formulas["add-2007-bl"]  # type: ignore
    with ctx.Pool(processes=1) as pool:
        res = pool.apply(formula_target, args=(formula,))
        assert res
    formula = formula.to_code()  # type: ignore
    with ctx.Pool(processes=1) as pool:
        res = pool.apply(formula_target, args=(formula,))
        assert res


def test_code_formula():
    sw = ShortWeierstrassModel()
    coords = sw.coordinates["projective"]
    formula = coords.formulas["add-2007-bl"]
    graph = FormulaGraph(formula)
    code = graph.to_formula()
    data = pickle.dumps(code)
    pickletools.dis(data)
    back = pickle.loads(data)
    assert code == back


def test_params(secp128r1):
    secp256r1 = get_params("secg", "secp256r1", "projective")
    params = (secp128r1, secp256r1)
    data = pickle.dumps(params)
    back = pickle.loads(data)
    assert params == back


def test_op(secp128r1):
    formula = secp128r1.curve.coordinate_model.formulas["add-2007-bl"]
    op = formula.code[0]
    data = pickle.dumps(op)
    back = pickle.loads(data)
    assert op == back
