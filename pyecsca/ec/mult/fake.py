from typing import List, Type, Callable

from pyecsca.ec.formula import Formula, AdditionFormula, DifferentialAdditionFormula, DoublingFormula, LadderFormula, \
    NegationFormula
from pyecsca.ec.formula.fake import FakeFormula
from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.params import DomainParameters


def fake_mult(mult_class: Type[ScalarMultiplier], mult_factory: Callable, params: DomainParameters) -> ScalarMultiplier:
    """
    Get a multiplier with FakeFormulas.

    :param mult_class: The class of the scalar multiplier to use.
    :param mult_factory: A callable that takes the formulas and instantiates the multiplier.
    :param params: The domain parameters to use.
    :return: The multiplier.
    """
    formula_classes: List[Type[Formula]] = list(
        filter(
            lambda klass: klass in mult_class.requires,
            [
                AdditionFormula,
                DifferentialAdditionFormula,
                DoublingFormula,
                LadderFormula,
                NegationFormula,
            ],
        )
    )
    formulas = []
    for formula in formula_classes:
        for subclass in formula.__subclasses__():
            if issubclass(subclass, FakeFormula):
                formulas.append(subclass(params.curve.coordinate_model))
    mult = mult_factory(*formulas, short_circuit=False)
    return mult
