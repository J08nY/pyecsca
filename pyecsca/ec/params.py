"""
Provides functions for obtaining domain parameters from the `std-curves <https://github.com/J08nY/std-curves>`_ repository [STD]_.

It also provides a domain parameter class and a class for a whole category of domain parameters.
"""
import json
import csv
from sympy import Poly, FF, symbols
from astunparse import unparse
from io import RawIOBase, BufferedIOBase
from pathlib import Path
from typing import Optional, Dict, Union, BinaryIO, List, Callable, IO
from importlib_resources import files

from public import public

from pyecsca.misc.cache import sympify
from pyecsca.ec.coordinates import AffineCoordinateModel, CoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.error import raise_unsatisified_assumption
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.model import (
    CurveModel,
    ShortWeierstrassModel,
    MontgomeryModel,
    EdwardsModel,
    TwistedEdwardsModel,
)
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.misc.cfg import getconfig


@public
class DomainParameters:
    """
    Domain parameters which specify a subgroup on an elliptic curve.

    >>> secp256r1 = get_params("secg", "secp256r1", "projective")
    >>> str(secp256r1)
    'DomainParameters(secg/secp256r1)'
    >>> secp256r1.order
    115792089210356248762697446949407573529996955224135760342422259061068512044369
    >>> secp256r1.cofactor
    1
    >>> secp256r1.generator
    Point([X=48439561293906451759052585252797914202762949526041747995844080717082404635286, Y=36134250956749795798585127919587881956611106672985015071877198253568414405109, Z=1] in shortw/projective)
    >>> secp256r1.curve.prime
    115792089210356248762697446949407573530086143415290314195533631308867097853951
    >>> secp256r1.curve.parameters  # doctest: +NORMALIZE_WHITESPACE
    {'a': 115792089210356248762697446949407573530086143415290314195533631308867097853948,
     'b': 41058363725152142129326129780047268409114441015993725554835256314039467401291}

    """

    curve: EllipticCurve
    generator: Point
    order: int
    cofactor: int
    name: Optional[str]
    category: Optional[str]

    def __init__(
        self,
        curve: EllipticCurve,
        generator: Point,
        order: int,
        cofactor: int,
        name: Optional[str] = None,
        category: Optional[str] = None,
    ):
        self.curve = curve
        self.generator = generator
        self.order = order
        self.cofactor = cofactor
        self.name = name
        self.category = category

    def __eq__(self, other):
        if not isinstance(other, DomainParameters):
            return False
        return (
            self.curve == other.curve
            and self.generator == other.generator
            and self.order == other.order
            and self.cofactor == other.cofactor
        )

    def __hash__(self):
        return hash((self.curve, self.generator, self.order, self.cofactor))

    def to_coords(self, coordinate_model: CoordinateModel) -> "DomainParameters":
        """
        Convert the domain parameters into a different coordinate model, only possible if they are currently affine.

        :param coordinate_model: The target coordinate model.
        :return: The transformed domain parameters
        """
        if not isinstance(self.curve.coordinate_model, AffineCoordinateModel):
            raise ValueError
        curve = self.curve.to_coords(coordinate_model)
        generator = self.generator.to_model(coordinate_model, curve)
        return DomainParameters(
            curve, generator, self.order, self.cofactor, self.name, self.category
        )

    def to_affine(self) -> "DomainParameters":
        """
        Convert the domain parameters into the affine coordinate model, if possible.

        :return: The transformed domain parameters
        """
        curve = self.curve.to_affine()
        generator = self.generator.to_affine()
        return DomainParameters(
            curve, generator, self.order, self.cofactor, self.name, self.category
        )

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
        return f"{self.__class__.__name__}({self.curve!r}, gen={self.generator!r}, ord={self.order}, cof={self.cofactor})"


@public
class DomainParameterCategory:
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
    params = {
        name: mod(int(curve["params"][name]["raw"], 16), field) for name in param_names
    }

    # Check coordinate model name and assumptions
    coord_model: CoordinateModel
    if coords == "affine":
        coord_model = AffineCoordinateModel(model)
    else:
        if coords not in model.coordinates:
            raise ValueError("Coordinate model not supported for curve model.")
        coord_model = model.coordinates[coords]
        for assumption in coord_model.assumptions:
            # Try to execute assumption, if it works, check with curve parameters
            # if it doesn't work, move all over to rhs and construct a sympy polynomial of it
            # then find roots and take first one for new value for new coordinate parameter.
            try:
                alocals: Dict[str, Union[Mod, int]] = {}
                compiled = compile(assumption, "", mode="exec")
                exec(compiled, None, alocals)  # exec is OK here, skipcq: PYL-W0122
                for param, value in alocals.items():
                    if params[param] != value:
                        raise_unsatisified_assumption(
                            getconfig().ec.unsatisfied_coordinate_assumption_action,
                            f"Coordinate model {coord_model} has an unsatisifed assumption on the {param} parameter (= {value}).",
                        )
            except NameError:
                k = FF(field)
                assumption_string = unparse(assumption).strip()
                lhs, rhs = assumption_string.split(" = ")
                expr = sympify(f"{rhs} - {lhs}")
                for curve_param, value in params.items():
                    expr = expr.subs(curve_param, value)
                if (
                    len(expr.free_symbols) > 1
                    or (param := str(expr.free_symbols.pop()))
                    not in coord_model.parameters
                ):
                    raise ValueError(
                        f"This coordinate model couldn't be loaded due to an unsupported assumption ({assumption_string})."
                    )
                numerator, _ = expr.as_numer_denom()
                poly = Poly(numerator, symbols(param), domain=k)
                roots = poly.ground_roots()
                for root in roots:
                    params[param] = mod(int(k.from_sympy(root)), field)
                    break
                else:
                    raise_unsatisified_assumption(
                        getconfig().ec.unsatisfied_coordinate_assumption_action,
                        f"Coordinate model {coord_model} has an unsatisifed assumption on the {param} parameter (0 = {expr} mod {field}).",
                    )

    # Construct the point at infinity
    infinity: Point
    if infty:
        infinity = InfinityPoint(coord_model)
    else:
        ilocals: Dict[str, Union[Mod, int]] = {**params}
        for line in coord_model.neutral:
            compiled = compile(line, "", mode="exec")
            exec(compiled, None, ilocals)  # exec is OK here, skipcq: PYL-W0122
        infinity_coords = {}
        for coordinate in coord_model.variables:
            if coordinate not in ilocals:
                raise ValueError(
                    f"Coordinate model {coord_model} requires infty option."
                )
            value = ilocals[coordinate]
            if isinstance(value, int):
                infinity_coords[coordinate] = mod(value, field)
            else:
                infinity_coords[coordinate] = value
        infinity = Point(coord_model, **infinity_coords)
    elliptic_curve = EllipticCurve(model, coord_model, field, infinity, params)  # type: ignore[arg-type]
    if "generator" not in curve:
        raise ValueError("Cannot construct curve, missing generator.")
    affine = Point(
        AffineCoordinateModel(model),
        x=mod(int(curve["generator"]["x"]["raw"], 16), field),
        y=mod(int(curve["generator"]["y"]["raw"], 16), field),
    )
    if not isinstance(coord_model, AffineCoordinateModel):
        generator = affine.to_model(coord_model, elliptic_curve)
    else:
        generator = affine
    return DomainParameters(
        elliptic_curve, generator, order, cofactor, curve["name"], curve["category"]
    )


@public
def load_category(
    file: Union[str, Path, BinaryIO, IO[bytes]],
    coords: Union[str, Callable[[str], str]],
    infty: Union[bool, Callable[[str], bool]] = True,
) -> DomainParameterCategory:
    """
    Load a category of domain parameters containing several curves from a JSON file.

    :param file: The file to load from.
    :param coords: The name of the coordinate system to use. Can be a callable that takes
                   as argument the name of the curve and produces the coordinate system to use for that curve.
    :param infty: Whether to use the special :py:class:`.InfinityPoint` (`True`) or try to use the
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
def load_params(
    file: Union[str, Path, BinaryIO], coords: str, infty: bool = True
) -> DomainParameters:
    """
    Load a curve from a JSON file.

    :param file: The file to load from.
    :param coords: The name of the coordinate system to use.
    :param infty: Whether to use the special :py:class:`.InfinityPoint` (`True`) or try to use the
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
def load_params_ecgen(
    file: Union[str, Path, BinaryIO], coords: str, infty: bool = True
) -> DomainParameters:
    """
    Load a curve from a file that is output of `ecgen <https://github.com/J08nY/ecgen>`_.

    :param file: The file to load from.
    :param coords: The name of the coordinate system to use.
    :param infty: Whether to use the special :py:class:`.InfinityPoint` (`True`) or try to use the
                  point at infinity of the coordinate system.
    :return: The curve.
    """
    if isinstance(file, (str, Path)):
        with open(file, "rb") as f:
            ecgen = json.load(f)
    elif isinstance(file, (RawIOBase, BufferedIOBase, BinaryIO)):
        ecgen = json.load(file)
    else:
        raise TypeError
    ecgen = ecgen[0]
    if "m" in ecgen["field"]:
        raise ValueError("Binary extension field curves not supported")
    if len(ecgen["subgroups"]) != 1:
        raise ValueError("Can not represent curve with two subgroups.")
    curve_dict = {
        "form": "Weierstrass",
        "field": {"type": "Prime", "p": ecgen["field"]["p"]},
        "order": ecgen["subgroups"][0]["order"],  # Take just the first subgroup
        "cofactor": ecgen["subgroups"][0]["cofactor"],
        "params": {"a": {"raw": ecgen["a"]}, "b": {"raw": ecgen["b"]}},
        "generator": {
            "x": {"raw": ecgen["subgroups"][0]["x"]},
            "y": {"raw": ecgen["subgroups"][0]["y"]},
        },
        "name": None,
        "category": None,
    }
    return _create_params(curve_dict, coords, infty)


@public
def load_params_ectester(
    file: Union[str, Path, BinaryIO], coords: str, infty: bool = True
) -> DomainParameters:
    """
    Load a curve from a file that uses the format of `ECTester <https://github.com/crocs-muni/ECTester>`_.

    :param file: The file to load from.
    :param coords: The name of the coordinate system to use.
    :param infty: Whether to use the special :py:class:`.InfinityPoint` (`True`) or try to use the
                  point at infinity of the coordinate system.
    :return: The curve.
    """
    if isinstance(file, (str, Path)):
        with open(file, "r") as f:
            reader = csv.reader(f)
            line = next(iter(reader))
    elif isinstance(file, (RawIOBase, BufferedIOBase, BinaryIO)):
        reader = csv.reader(list(map(lambda line: line.decode(), file.readlines())))
        line = next(iter(reader))
    else:
        raise TypeError
    if len(line) != 7:
        raise ValueError("Binary extension field curves not supported")
    # p,a,b,gx,gy,n,h (all in hex)
    curve_dict = {
        "form": "Weierstrass",
        "field": {"type": "Prime", "p": line[0]},
        "order": line[5],
        "cofactor": line[6],
        "params": {"a": {"raw": line[1]}, "b": {"raw": line[2]}},
        "generator": {"x": {"raw": line[3]}, "y": {"raw": line[4]}},
        "name": None,
        "category": None,
    }
    return _create_params(curve_dict, coords, infty)


@public
def get_category(
    category: str,
    coords: Union[str, Callable[[str], str]],
    infty: Union[bool, Callable[[str], bool]] = True,
) -> DomainParameterCategory:
    """
    Retrieve a category from the std-curves database at https://github.com/J08nY/std-curves.

    :param category: The category to retrieve.
    :param coords: The name of the coordinate system to use. Can be a callable that takes
                   as argument the name of the curve and produces the coordinate system to use for that curve.
    :param infty: Whether to use the special :py:class:`.InfinityPoint` (`True`) or try to use the
                  point at infinity of the coordinate system. Can be a callable that takes
                  as argument the name of the curve and returns the infinity option to use for that curve.
    :return: The category.
    """
    categories = {
        entry.name: entry
        for entry in files("pyecsca.ec").joinpath("std").iterdir()
        if entry.is_dir()
    }
    if category not in categories:
        raise ValueError(f"Category {category} not found.")
    with categories[category].joinpath("curves.json").open("rb") as f:
        return load_category(f, coords, infty)


@public
def get_params(
    category: str, name: str, coords: str, infty: bool = True
) -> DomainParameters:
    """
    Retrieve a curve from a set of stored parameters.

    Uses the std-curves database at https://github.com/J08nY/std-curves.

    :param category: The category of the curve.
    :param name: The name of the curve.
    :param coords: The name of the coordinate system to use.
    :param infty: Whether to use the special :py:class:`.InfinityPoint` (`True`) or try to use the
                  point at infinity of the coordinate system.
    :return: The curve.
    """
    categories = {
        entry.name: entry
        for entry in files("pyecsca.ec").joinpath("std").iterdir()
        if entry.is_dir()
    }
    if category not in categories:
        raise ValueError(f"Category {category} not found.")
    with categories[category].joinpath("curves.json").open("rb") as f:
        category_json = json.load(f)
    curve = None
    for curve in category_json["curves"]:
        if curve["name"] == name:
            break
    else:
        raise ValueError(f"Curve {name} not found in category {category}.")

    return _create_params(curve, coords, infty)


_dirs = list(files("pyecsca.ec").joinpath("std").iterdir())
if not _dirs:
    import warnings

    warnings.warn(
        "std-curves repository is not available. pyecsca is mis-installed. "
        "Make sure that you check out the git submodules prior to install (when installing from git)."
    )
