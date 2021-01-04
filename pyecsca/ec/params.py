import json
from sympy import Poly, FF, symbols, sympify
from astunparse import unparse
from io import RawIOBase, BufferedIOBase
from os.path import join
from pathlib import Path
from typing import Optional, Dict, Union, BinaryIO, List, Callable

from pkg_resources import resource_listdir, resource_isdir, resource_stream
from public import public

from .coordinates import AffineCoordinateModel, CoordinateModel
from .curve import EllipticCurve
from .error import UnsatisfiedAssumptionError, raise_unsatisified_assumption
from .mod import Mod
from .model import (CurveModel, ShortWeierstrassModel, MontgomeryModel, EdwardsModel,
                    TwistedEdwardsModel)
from .point import Point, InfinityPoint
from ..misc.cfg import getconfig


@public
class DomainParameters(object):
    """Domain parameters which specify a subgroup on an elliptic curve."""
    curve: EllipticCurve
    generator: Point
    order: int
    cofactor: int
    name: Optional[str]
    category: Optional[str]

    def __init__(self, curve: EllipticCurve, generator: Point, order: int,
                 cofactor: int, name: Optional[str] = None, category: Optional[str] = None):
        self.curve = curve
        self.generator = generator
        self.order = order
        self.cofactor = cofactor
        self.name = name
        self.category = category

    def __eq__(self, other):
        if not isinstance(other, DomainParameters):
            return False
        return self.curve == other.curve and self.generator == other.generator and self.order == other.order and self.cofactor == other.cofactor

    def __get_name(self):
        if self.name and self.category:
            return f"{self.category}/{self.name}"
        elif self.name:
            return self.name
        elif self.category:
            return self.category
        return ""

    def __str__(self):
        name = self.__get_name()
        if not name:
            name = str(self.curve)
        return f"{self.__class__.__name__}({name})"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.curve!r}, {self.generator!r}, {self.order}, {self.cofactor})"


@public
class DomainParameterCategory(object):
    """A category of domain parameters."""
    name: str
    description: str
    curves: List[DomainParameters]

    def __init__(self, name: str, description: str, curves: List[DomainParameters]):
        self.name = name
        self.description = description
        self.curves = curves

    def __str__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __iter__(self):
        yield from self.curves

    def __contains__(self, item):
        return item in self.curves

    def __len__(self):
        return len(self.curves)

    def __getitem__(self, item):
        return self.curves[item]


def _create_params(curve, coords, infty):
    if curve["field"]["type"] == "Binary":
        raise ValueError("Binary field curves are currently not supported.")
    if curve["field"]["type"] == "Extension":
        raise ValueError("Extension field curves are currently not supported.")

    # Get model and param names
    model: CurveModel
    field = int(curve["field"]["p"], 16)
    order = int(curve["order"], 16)
    cofactor = int(curve["cofactor"], 16)
    if curve["form"] == "Weierstrass":
        model = ShortWeierstrassModel()
        param_names = ["a", "b"]
    elif curve["form"] == "Montgomery":
        model = MontgomeryModel()
        param_names = ["a", "b"]
    elif curve["form"] == "Edwards":
        model = EdwardsModel()
        param_names = ["c", "d"]
    elif curve["form"] == "TwistedEdwards":
        model = TwistedEdwardsModel()
        param_names = ["a", "d"]
    else:
        raise ValueError("Unknown curve model.")
    params = {name: Mod(int(curve["params"][name]["raw"], 16), field) for name in param_names}

    # Check coordinate model name and assumptions
    coord_model: CoordinateModel
    if coords == "affine":
        coord_model = AffineCoordinateModel(model)
    else:
        if coords not in model.coordinates:
            raise ValueError("Coordinate model not supported for curve.")
        coord_model = model.coordinates[coords]
        for assumption in coord_model.assumptions:
            # Try to execute assumption, if it works, check with curve parameters
            # if it doesn't work, move all over to rhs and construct a sympy polynomial of it
            # then find roots and take first one for new value for new coordinate parameter.
            try:
                alocals: Dict[str, Union[Mod, int]] = {}
                compiled = compile(assumption, "", mode="exec")
                exec(compiled, None, alocals)
                for param, value in alocals.items():
                    if params[param] != value:
                        raise_unsatisified_assumption(getconfig().ec.unsatisfied_coordinate_assumption_action,
                                                      f"Coordinate model {coord_model} has an unsatisifed assumption on the {param} parameter (= {value}).")
            except NameError:
                k = FF(field)
                assumption_string = unparse(assumption)
                lhs, rhs = assumption_string.split(" = ")
                expr = sympify(f"{rhs} - {lhs}")
                for curve_param, value in params.items():
                    expr = expr.subs(curve_param, k(value))
                if len(expr.free_symbols) > 1 or (param := str(expr.free_symbols.pop())) not in coord_model.parameters:
                    raise ValueError(f"This coordinate model couldn't be loaded due to an unsupported assumption ({assumption_string}).")
                poly = Poly(expr, symbols(param), domain=k)
                roots = poly.ground_roots()
                for root in roots.keys():
                    params[param] = Mod(int(root), field)
                    break
                else:
                    raise UnsatisfiedAssumptionError(f"Coordinate model {coord_model} has an unsatisifed assumption on the {param} parameter (0 = {expr}).")

    # Construct the point at infinity
    infinity: Point
    if infty:
        infinity = InfinityPoint(coord_model)
    else:
        ilocals: Dict[str, Union[Mod, int]] = {**params}
        for line in coord_model.neutral:
            compiled = compile(line, "", mode="exec")
            exec(compiled, None, ilocals)
        infinity_coords = {}
        for coordinate in coord_model.variables:
            if coordinate not in ilocals:
                raise ValueError(f"Coordinate model {coord_model} requires infty option.")
            value = ilocals[coordinate]
            if isinstance(value, int):
                value = Mod(value, field)
            infinity_coords[coordinate] = value
        infinity = Point(coord_model, **infinity_coords)
    elliptic_curve = EllipticCurve(model, coord_model, field, infinity, params)  # type: ignore[arg-type]
    affine = Point(AffineCoordinateModel(model),
                   x=Mod(int(curve["generator"]["x"]["raw"], 16), field),
                   y=Mod(int(curve["generator"]["y"]["raw"], 16), field))
    if not isinstance(coord_model, AffineCoordinateModel):
        generator = affine.to_model(coord_model, elliptic_curve)
    else:
        generator = affine
    return DomainParameters(elliptic_curve, generator, order, cofactor, curve["name"], curve["category"])


@public
def load_category(file: Union[str, Path, BinaryIO], coords: Union[str, Callable[[str], str]],
                  infty: Union[bool, Callable[[str], bool]] = True) -> DomainParameterCategory:
    """
    Load a category of domain parameters containing several curves from a JSON file.

    :param file: The file to load from.
    :param coords: The name of the coordinate system to use. Can be a callable that takes
                   as argument the name of the curve and produces the coordinate system to use for that curve.
    :param infty: Whether to use the special :py:class:InfinityPoint (`True`) or try to use the
                  point at infinity of the coordinate system. Can be a callable that takes
                  as argument the name of the curve and returns the infinity option to use for that curve.
    :return: The category.
    """
    if isinstance(file, (str, Path)):
        with open(file, "rb") as f:
            data = json.load(f)
    elif isinstance(file, (RawIOBase, BufferedIOBase, BinaryIO)):
        data = json.load(file)
    else:
        raise TypeError

    curves = []
    for curve_data in data["curves"]:
        curve_coords = coords(curve_data["name"]) if callable(coords) else coords
        curve_infty = infty(curve_data["name"]) if callable(infty) else infty
        try:
            curve = _create_params(curve_data, curve_coords, curve_infty)
        except ValueError:
            continue
        curves.append(curve)

    return DomainParameterCategory(data["name"], data["desc"], curves)


@public
def load_params(file: Union[str, Path, BinaryIO], coords: str, infty: bool = True) -> DomainParameters:
    """
    Load a curve from a JSON file.

    :param file: The file to load from.
    :param coords: The name of the coordinate system to use.
    :param infty: Whether to use the special :py:class:InfinityPoint (`True`) or try to use the
                  point at infinity of the coordinate system.
    :return: The curve.
    """
    if isinstance(file, (str, Path)):
        with open(file, "rb") as f:
            curve = json.load(f)
    elif isinstance(file, (RawIOBase, BufferedIOBase, BinaryIO)):
        curve = json.load(file)
    else:
        raise TypeError

    return _create_params(curve, coords, infty)


@public
def get_category(category: str, coords: Union[str, Callable[[str], str]],
                 infty: Union[bool, Callable[[str], bool]] = True) -> DomainParameterCategory:
    """
    Retrieve a category from the std-curves database at https://github.com/J08nY/std-curves.

    :param category: The category to retrieve.
    :param coords: The name of the coordinate system to use. Can be a callable that takes
                   as argument the name of the curve and produces the coordinate system to use for that curve.
    :param infty: Whether to use the special :py:class:InfinityPoint (`True`) or try to use the
                  point at infinity of the coordinate system. Can be a callable that takes
                  as argument the name of the curve and returns the infinity option to use for that curve.
    :return: The category.
    """
    listing = resource_listdir(__name__, "std")
    categories = list(entry for entry in listing if resource_isdir(__name__, join("std", entry)))
    if category not in categories:
        raise ValueError(f"Category {category} not found.")
    json_path = join("std", category, "curves.json")
    with resource_stream(__name__, json_path) as f:
        return load_category(f, coords, infty)


@public
def get_params(category: str, name: str, coords: str, infty: bool = True) -> DomainParameters:
    """
    Retrieve a curve from a set of stored parameters. Uses the std-curves database at
    https://github.com/J08nY/std-curves.

    :param category: The category of the curve.
    :param name: The name of the curve.
    :param coords: The name of the coordinate system to use.
    :param infty: Whether to use the special :py:class:InfinityPoint (`True`) or try to use the
                  point at infinity of the coordinate system.
    :return: The curve.
    """
    listing = resource_listdir(__name__, "std")
    categories = list(entry for entry in listing if resource_isdir(__name__, join("std", entry)))
    if category not in categories:
        raise ValueError(f"Category {category} not found.")
    json_path = join("std", category, "curves.json")
    with resource_stream(__name__, json_path) as f:
        category_json = json.load(f)
    for curve in category_json["curves"]:
        if curve["name"] == name:
            break
    else:
        raise ValueError(f"Curve {name} not found in category {category}.")

    return _create_params(curve, coords, infty)
