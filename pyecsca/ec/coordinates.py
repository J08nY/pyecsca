"""Provides a coordinate model class."""
from ast import parse, Module
from importlib_resources.abc import Traversable
from importlib_resources import as_file
from typing import List, Any, MutableMapping

from public import public

from pyecsca.ec.formula.base import Formula
from pyecsca.ec.formula.efd import (
    EFDFormula,
    AdditionEFDFormula,
    DoublingEFDFormula,
    TriplingEFDFormula,
    DifferentialAdditionEFDFormula,
    LadderEFDFormula,
    ScalingEFDFormula,
    NegationEFDFormula,
)


@public
class CoordinateModel:
    """
    A coordinate system for a particular model(form) of an elliptic curve.

    >>> from pyecsca.ec.params import get_params
    >>> params = get_params("secg", "secp256r1", "projective")
    >>> coordinate_model = params.curve.coordinate_model
    >>> coordinate_model
    EFDCoordinateModel("projective", curve_model=ShortWeierstrass)
    >>> coordinate_model.variables
    ['X', 'Y', 'Z']
    >>> coordinate_model.curve_model
    ShortWeierstrassModel()
    >>> sorted(coordinate_model.formulas.items())  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
    [('add-1998-cmo', AdditionEFDFormula(add-1998-cmo for shortw/projective)),
     ('add-1998-cmo-2', AdditionEFDFormula(add-1998-cmo-2 for shortw/projective)),
     ...
     ('dbl-2007-bl', DoublingEFDFormula(dbl-2007-bl for shortw/projective)),
     ...]
    """

    name: str
    """Name of the coordinate model"""
    full_name: str
    """Full name."""
    curve_model: Any
    """The curve model."""
    variables: List[str]
    """Variables that the coordinate model uses."""
    satisfying: List[Module]
    """Relationship between the coordinate system and affine coordinates."""
    toaffine: List[Module]
    """Map to affine coordinates from system coordinates."""
    tosystem: List[Module]
    """Map from coordinate system to affine coordinates."""
    homogweights: MutableMapping[str, int]
    """Weights that homogenize the coordinates."""
    parameters: List[str]
    """Coordinate system parameters."""
    assumptions: List[Module]
    """Assumptions that need to hold for the curve to use this coordinate system,
    also used to compute the values of the coordinate system parameters."""
    neutral: List[Module]
    """Coordinates of the neutral point in the coordinate system, might contain expressions of parameters."""
    formulas: MutableMapping[str, Formula]
    """Formulas available on the coordinate system."""

    def __str__(self):
        return f"{self.curve_model.shortname}/{self.name}"

    def __repr__(self):
        return (
            f'{self.__class__.__name__}("{self.name}", curve_model={self.curve_model})'
        )


@public
class AffineCoordinateModel(CoordinateModel):
    """An affine coordinate model (there is really only one per curve model)."""

    name = "affine"
    full_name = "Affine coordinates"

    def __init__(self, curve_model: Any):
        self.curve_model = curve_model
        self.variables = ["x", "y"]
        self.satisfying = []
        self.toaffine = []
        self.tosystem = []
        self.parameters = []
        self.assumptions = []
        self.neutral = []
        self.formulas = {}

    def __eq__(self, other):
        if not isinstance(other, AffineCoordinateModel):
            return False
        return self.curve_model == other.curve_model

    def __hash__(self):
        return hash((self.curve_model, self.name))


class EFDCoordinateModel(CoordinateModel):
    """A coordinate model from [EFD]_ data."""

    def __new__(cls, *args, **kwargs):
        _, name, curve_model = args
        if name in curve_model.coordinates:
            return curve_model.coordinates[name]
        return object.__new__(cls)

    def __init__(self, dir_path: Traversable, name: str, curve_model: Any):
        self.name = name
        self.curve_model = curve_model
        self.variables = []
        self.satisfying = []
        self.toaffine = []
        self.tosystem = []
        self.homogweights = {}
        self.parameters = []
        self.assumptions = []
        self.neutral = []
        self.formulas = {}
        for entry in dir_path.iterdir():
            with as_file(entry) as file_path:
                if entry.is_dir():
                    self.__read_formula_dir(file_path, file_path.stem)
                else:
                    self.__read_coordinates_file(file_path)

    def __read_formula_dir(self, dir_path: Traversable, formula_type):
        for entry in dir_path.iterdir():
            with as_file(entry) as fpath:
                if fpath.suffix == ".op3":
                    continue
                formula_types = {
                    "addition": AdditionEFDFormula,
                    "doubling": DoublingEFDFormula,
                    "tripling": TriplingEFDFormula,
                    "diffadd": DifferentialAdditionEFDFormula,
                    "ladder": LadderEFDFormula,
                    "scaling": ScalingEFDFormula,
                    "negation": NegationEFDFormula,
                }
                cls = formula_types.get(formula_type, EFDFormula)
                self.formulas[fpath.stem] = cls(
                    fpath, fpath.with_suffix(".op3"), fpath.stem, self
                )

    def __read_coordinates_file(self, file_path: Traversable):
        with file_path.open("rb") as f:
            line = f.readline().decode("ascii").rstrip()
            while line:
                if line.startswith("name"):
                    self.full_name = line[5:]
                elif line.startswith("variable"):
                    self.variables.append(line[9:])
                elif line.startswith("neutral"):
                    try:
                        code = parse(line[8:].replace("^", "**"), mode="exec")
                        self.neutral.append(code)
                    except SyntaxError:
                        pass
                elif line.startswith("satisfying"):
                    try:
                        code = parse(line[11:].replace("^", "**"), mode="exec")
                        self.satisfying.append(code)
                    except SyntaxError:
                        pass
                elif line.startswith("toaffine"):
                    try:
                        code = parse(line[9:].replace("^", "**"), mode="exec")
                        self.toaffine.append(code)
                    except SyntaxError:
                        pass
                elif line.startswith("tosystem"):
                    try:
                        code = parse(line[9:].replace("^", "**"), mode="exec")
                        self.tosystem.append(code)
                    except SyntaxError:
                        pass
                elif line.startswith("homogweight"):
                    try:
                        var, weight = line[11:].split("=")
                        self.homogweights[var.strip()] = int(weight)
                    except SyntaxError:
                        pass
                elif line.startswith("parameter"):
                    self.parameters.append(line[10:])
                elif line.startswith("assume"):
                    self.assumptions.append(
                        parse(line[7:].replace("^", "**"), mode="exec")
                    )
                line = f.readline().decode("ascii").rstrip()

    def __getnewargs__(self):
        return None, self.name, self.curve_model

    def __getstate__(self):
        return {}

    def __eq__(self, other):
        if not isinstance(other, EFDCoordinateModel):
            return False
        return self.curve_model == other.curve_model and self.name == other.name

    def __hash__(self):
        return hash((self.curve_model, self.name))
