from ast import parse, Expression, Module
from pkg_resources import resource_listdir, resource_isdir, resource_stream
from public import public
from typing import List, MutableMapping

from .coordinates import CoordinateModel


class CurveModel(object):
    _efd_name: str
    _loaded: bool = False
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

    def __init__(self, efd_name: str):
        self._efd_name = efd_name
        if self._loaded:
            return
        else:
            self.__class__._loaded = True
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

        files = resource_listdir(__name__, "efd/" + efd_name)
        for fname in files:
            file_path = "efd/" + efd_name + "/" + fname
            if resource_isdir(__name__, file_path):
                self.__read_coordinate_dir(file_path, fname)
            else:
                self.__read_curve_file(self.__class__, file_path)

    def __read_curve_file(self, cls, file_path):
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
                    cls.from_weierstrass.append(format_eq(line[16:]))
                else:
                    cls.full_weierstrass.append(format_eq(line))
                line = f.readline()

    def __read_coordinate_dir(self, dir_path, name):
        self.coordinates[name] = CoordinateModel(dir_path, name, self)


@public
class ShortWeierstrassModel(CurveModel):

    def __init__(self):
        super().__init__("shortw")


@public
class MontgomeryModel(CurveModel):

    def __init__(self):
        super().__init__("montgom")


@public
class EdwardsModel(CurveModel):

    def __init__(self):
        super().__init__("edwards")


@public
class TwistedEdwardsModel(CurveModel):

    def __init__(self):
        super().__init__("twisted")
