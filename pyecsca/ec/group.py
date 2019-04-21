from typing import Optional

from public import public

from .curve import EllipticCurve
from .point import Point


@public
class AbelianGroup(object):
    curve: EllipticCurve
    generator: Point
    neutral: Point
    order: Optional[int]
    cofactor: Optional[int]

    def __init__(self, curve: EllipticCurve, generator: Point, neutral: Point, order: int = None,
                 cofactor: int = None):
        self.curve = curve
        self.generator = generator
        self.neutral = neutral
        self.order = order
        self.cofactor = cofactor

    def is_neutral(self, point: Point) -> bool:
        return self.neutral == point
