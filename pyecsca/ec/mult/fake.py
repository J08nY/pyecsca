from typing import Type, Callable
from copy import deepcopy

from pyecsca.ec.formula import (
    AdditionFormula,
    DifferentialAdditionFormula,
    DoublingFormula,
    LadderFormula,
    NegationFormula,
    ScalingFormula,
)
from pyecsca.ec.formula.fake import FakeAdditionFormula, FakeDifferentialAdditionFormula, \
    FakeDoublingFormula, FakeLadderFormula, FakeNegationFormula, FakeScalingFormula
from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.params import DomainParameters


fake_map = {
    AdditionFormula: FakeAdditionFormula,
    DifferentialAdditionFormula: FakeDifferentialAdditionFormula,
    DoublingFormula: FakeDoublingFormula,
    LadderFormula: FakeLadderFormula,
    NegationFormula: FakeNegationFormula,
    ScalingFormula: FakeScalingFormula,
}


def fake_mult(
    mult_class: Type[ScalarMultiplier], mult_factory: Callable, params: DomainParameters
) -> ScalarMultiplier:
    """
    Get a multiplier with `FakeFormula`s.

    :param mult_class: The class of the scalar multiplier to use.
    :param mult_factory: A callable that takes the formulas and instantiates the multiplier.
    :param params: The domain parameters to use.
    :return: The multiplier.
    """
    formulas = []
    for formula, fake_formula in fake_map.items():
        if formula in mult_class.requires:
            formulas.append(fake_formula(params.curve.coordinate_model))
    mult = mult_factory(*formulas, short_circuit=False)
    return mult


def turn_fake(mult: ScalarMultiplier) -> ScalarMultiplier:
    """
    Turn a multiplier into a fake multiplier.

    :param mult: The multiplier to turn into a fake multiplier.
    :return: The multiplier with fake formulas.
    """
    copy = deepcopy(mult)
    copy.short_circuit = False
    formulas = {}
    for key, formula in copy.formulas.items():
        for real, fake in fake_map.items():
            if isinstance(formula, real):
                formulas[key] = fake(formula.coordinate_model)
    copy.formulas = formulas
    return copy
