import json
from os.path import join

from pkg_resources import resource_listdir, resource_isdir, resource_stream
from public import public

from .coordinates import AffineCoordinateModel
from .curve import EllipticCurve
from .mod import Mod
from .model import (ShortWeierstrassModel, MontgomeryModel, TwistedEdwardsModel,
                    EdwardsModel, CurveModel)
from .params import DomainParameters
from .point import Point, InfinityPoint


@public
def get_params(category: str, name: str, coords: str) -> DomainParameters:
    """
    Retrieve a curve from a set of stored parameters. Uses the std-curves database at
    https://github.com/J08nY/std-curves.

    :param category: The category of the curve.
    :param name: The name of the curve.
    :param coords: The name of the coordinate system to use.
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
    if coords not in model.coordinates:
        raise ValueError("Coordinate model not supported for curve.")
    coord_model = model.coordinates[coords]
    params = {name: Mod(int(curve["params"][name], 16), field) for name in param_names}
    for assumption in coord_model.assumptions:
        locals = {}
        compiled = compile(assumption, "", mode="exec")
        exec(compiled, None, locals)
        for param, value in locals.items():
            if params[param] != value:
                raise ValueError(f"Coordinate model {coord_model} has an unsatisifed assumption on the {param} parameter (= {value}).")
    elliptic_curve = EllipticCurve(model, coord_model, field, InfinityPoint(coord_model), params)
    affine = Point(AffineCoordinateModel(model), x=Mod(int(curve["generator"]["x"], 16), field),
                   y=Mod(int(curve["generator"]["y"], 16), field))
    generator = Point.from_affine(coord_model, affine)
    return DomainParameters(elliptic_curve, generator, order, cofactor, name, category)
