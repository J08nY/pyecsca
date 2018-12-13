from ast import parse, Expression, Module
from pkg_resources import resource_listdir, resource_isdir, resource_stream
from public import public
from typing import List, MutableMapping

from .coordinates import CoordinateModel


class CurveModel(object):
    _efd_name: str
    name: str
    coordinates: MutableMapping[str, CoordinateModel]
    parameter_names: List[str]
    coordinate_names: List[str]
    equation: Expression
    base_addition: List[Module]
    base_doubling: List[Module]
    base_negation: List[Module]
    base_neutral: List[Module]
    full_weierstrass: List[Module]
    to_weierstrass: List[Module]
    from_weierstrass: List[Module]

    def __init_subclass__(cls, efd_name: str = "", **kwargs):
        cls._efd_name = efd_name
        files = resource_listdir(__name__, "efd/" + efd_name)
        cls.coordinates = {}
        cls.parameter_names = []
        cls.coordinate_names = []
        cls.base_addition = []
        cls.base_doubling = []
        cls.base_negation = []
        cls.base_neutral = []
        cls.full_weierstrass = []
        cls.to_weierstrass = []
        cls.from_weierstrass = []
        for fname in files:
            file_path = "efd/" + efd_name + "/" + fname
            if resource_isdir(__name__, file_path):
                cls.__read_coordinate_dir(file_path, fname)
            else:
                cls.__read_curve_file(file_path)

    @classmethod
    def __read_curve_file(cls, file_path):
        def format_eq(line, mode="exec"):
            return parse(line.replace("^", "**"), mode=mode)

        with resource_stream(__name__, file_path) as f:
            line = f.readline()
            while line:
                line = line.decode("ascii")[:-1]
                if line.startswith("name"):
                    cls.name = line[5:]
                elif line.startswith("parameter"):
                    cls.parameter_names.append(line[10:])
                elif line.startswith("coordinate"):
                    cls.coordinate_names.append(line[11:])
                elif line.startswith("satisfying"):
                    cls.equation = format_eq(line[11:], mode="eval")
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
                    cls.to_weierstrass.append(format_eq(line[16:]))
                else:
                    cls.full_weierstrass.append(format_eq(line))
                line = f.readline()

    @classmethod
    def __read_coordinate_dir(cls, dir_path, name):
        cls.coordinates[name] = CoordinateModel(dir_path, name, cls)


@public
class ShortWeierstrassModel(CurveModel, efd_name="shortw"):
    pass


@public
class MontgomeryModel(CurveModel, efd_name="montgom"):
    pass


@public
class EdwardsModel(CurveModel, efd_name="edwards"):
    pass


@public
class TwistedEdwardsModel(CurveModel, efd_name="twisted"):
    pass
