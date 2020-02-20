from typing import Optional

from public import public

from .curve import EllipticCurve
from .point import Point


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
