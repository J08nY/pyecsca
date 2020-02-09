from public import public

from .curve import EllipticCurve
from .point import Point


@public
class DomainParameters(object):
    """A (sub)group of an elliptic curve."""
    curve: EllipticCurve
    generator: Point
    neutral: Point
    order: int
    cofactor: int

    def __init__(self, curve: EllipticCurve, generator: Point, neutral: Point, order: int,
                 cofactor: int):
        self.curve = curve
        self.generator = generator
        self.neutral = neutral
        self.order = order
        self.cofactor = cofactor

    def is_neutral(self, point: Point) -> bool:
        return self.neutral == point

    def __eq__(self, other):
        if not isinstance(other, DomainParameters):
            return False
        return self.curve == other.curve and self.generator == other.generator and self.neutral == other.neutral and self.order == other.order and self.cofactor == other.cofactor
