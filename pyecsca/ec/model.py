"""Provides curve model classes for the supported curve models."""
from ast import parse, Expression, Module
from typing import List, MutableMapping
from importlib_resources import files, as_file
from importlib_resources.abc import Traversable

from public import public

from pyecsca.ec.coordinates import EFDCoordinateModel, CoordinateModel


@public
class CurveModel:
    """Model(form) of an elliptic curve."""

    name: str
    shortname: str
    coordinates: MutableMapping[str, CoordinateModel]
    parameter_names: List[str]
    coordinate_names: List[str]
    equation: Expression
    ysquared: Expression
    base_addition: List[Module]
    base_doubling: List[Module]
    base_negation: List[Module]
    base_neutral: List[Module]
    full_weierstrass: List[Module]
    to_weierstrass: List[Module]
    from_weierstrass: List[Module]


class EFDCurveModel(CurveModel):
    """A curve model from [EFD]_ data."""

    _efd_name: str
    _loaded: bool = False

    def __init__(self, efd_name: str):
        self._efd_name = efd_name
        self.shortname = efd_name
        if self._loaded:
            return
        self.__load(efd_name)

    def __load(self, efd_name: str):
        self.__class__._loaded = True  # skipcq: PYL-W0212
        self.__class__.coordinates = {}
        self.__class__.parameter_names = []
        self.__class__.coordinate_names = []
        self.__class__.base_addition = []
        self.__class__.base_doubling = []
        self.__class__.base_negation = []
        self.__class__.base_neutral = []
        self.__class__.full_weierstrass = []
        self.__class__.to_weierstrass = []
        self.__class__.from_weierstrass = []

        for entry in files("pyecsca.ec").joinpath("efd", efd_name).iterdir():
            with as_file(entry) as file_path:
                if entry.is_dir():
                    self.__read_coordinate_dir(
                        self.__class__, file_path, file_path.stem
                    )
                else:
                    self.__read_curve_file(self.__class__, file_path)

    def __read_curve_file(self, cls, file_path: Traversable):
        def format_eq(line, mode="exec"):
            return parse(line.replace("^", "**"), mode=mode)

        with file_path.open("rb") as f:
            for raw in f.readlines():
                line = raw.decode("ascii").rstrip()
                if line.startswith("name"):
                    cls.name = line[5:]
                elif line.startswith("parameter"):
                    cls.parameter_names.append(line[10:])
                elif line.startswith("coordinate"):
                    cls.coordinate_names.append(line[11:])
                elif line.startswith("satisfying"):
                    cls.equation = format_eq(line[11:], mode="eval")
                elif line.startswith("ysquared"):
                    cls.ysquared = format_eq(line[9:], mode="eval")
                elif line.startswith("addition"):
                    cls.base_addition.append(format_eq(line[9:]))
                elif line.startswith("doubling"):
                    cls.base_doubling.append(format_eq(line[9:]))
                elif line.startswith("negation"):
                    cls.base_negation.append(format_eq(line[9:]))
                elif line.startswith("neutral"):
                    cls.base_neutral.append(format_eq(line[8:]))
                elif line.startswith("toweierstrass"):
                    cls.to_weierstrass.append(format_eq(line[14:]))
                elif line.startswith("fromweierstrass"):
                    cls.from_weierstrass.append(format_eq(line[16:]))
                else:
                    cls.full_weierstrass.append(format_eq(line))

    def __read_coordinate_dir(self, cls, dir_path: Traversable, name: str):
        cls.coordinates[name] = EFDCoordinateModel(dir_path, name, self)

    def __eq__(self, other):
        if not isinstance(other, EFDCurveModel):
            return False
        return self._efd_name == other._efd_name

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, state):
        if not self.__class__._loaded:
            self.__load(state["_efd_name"])
        self.__dict__.update(state)

    def __hash__(self):
        return hash(self._efd_name)

    def __str__(self):
        return f"{self.__class__.__name__.replace('Model', '')}"

    def __repr__(self):
        return f"{self.__class__.__name__}()"


@public
class ShortWeierstrassModel(EFDCurveModel):
    """
    Short-Weierstrass curve model.

    .. math::

       y^2 = x^3 + a x + b
    """

    def __init__(self):
        super().__init__("shortw")


@public
class MontgomeryModel(EFDCurveModel):
    """
    Montgomery curve model.

    .. math::

       B y^2 = x^3 + A x^2 + x
    """

    def __init__(self):
        super().__init__("montgom")


@public
class EdwardsModel(EFDCurveModel):
    """
    Edwards curve model.

    .. math::

       x^2 + y^2 = c^2 (1 + d x^2 y^2)
    """

    def __init__(self):
        super().__init__("edwards")


@public
class TwistedEdwardsModel(EFDCurveModel):
    """
    Twisted-Edwards curve model.

    .. math::

       a x^2 + y^2 = 1 + d x^2 y^2
    """

    def __init__(self):
        super().__init__("twisted")


_dirs = list(files("pyecsca.ec").joinpath("efd").iterdir())
if not _dirs:
    import warnings

    warnings.warn(
        "EFD not available, pyecsca is mis-installed. "
        "Make sure that you check out the git submodules prior to install (when installing from git)."
    )
