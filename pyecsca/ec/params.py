import json
from os.path import join
from typing import Optional, Dict, Union

from pkg_resources import resource_listdir, resource_isdir, resource_stream
from public import public

from .coordinates import AffineCoordinateModel, CoordinateModel
from .curve import EllipticCurve
from .mod import Mod
from .model import (CurveModel, ShortWeierstrassModel, MontgomeryModel, EdwardsModel,
                    TwistedEdwardsModel)
from .point import Point, InfinityPoint


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
        raise ValueError("Category {} not found.".format(category))
    json_path = join("std", category, "curves.json")
    with resource_stream(__name__, json_path) as f:
        category_json = json.load(f)
    for curve in category_json["curves"]:
        if curve["name"] == name:
            break
    else:
        raise ValueError("Curve {} not found in category {}.".format(name, category))
    if curve["field"]["type"] == "Binary":
        raise ValueError("Binary field curves are currently not supported.")

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
    params = {name: Mod(int(curve["params"][name], 16), field) for name in param_names}

    # Check coordinate model name and assumptions
    coord_model: CoordinateModel
    if coords == "affine":
        coord_model = AffineCoordinateModel(model)
    else:
        if coords not in model.coordinates:
            raise ValueError("Coordinate model not supported for curve.")
        coord_model = model.coordinates[coords]
        for assumption in coord_model.assumptions:
            alocals: Dict[str, Union[Mod, int]] = {}
            compiled = compile(assumption, "", mode="exec")
            exec(compiled, None, alocals)
            for param, value in alocals.items():
                if params[param] != value:
                    raise ValueError(f"Coordinate model {coord_model} has an unsatisifed assumption on the {param} parameter (= {value}).")

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
    elliptic_curve = EllipticCurve(model, coord_model, field, infinity, params) # type: ignore[arg-type]
    affine = Point(AffineCoordinateModel(model), x=Mod(int(curve["generator"]["x"], 16), field),
                   y=Mod(int(curve["generator"]["y"], 16), field))
    if not isinstance(coord_model, AffineCoordinateModel):
        generator = Point.from_affine(coord_model, affine)
    else:
        generator = affine
    return DomainParameters(elliptic_curve, generator, order, cofactor, name, category)