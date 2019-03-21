from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel
from pyecsca.ec.point import InfinityPoint, Point


def get_secp128r1():
    prime = 0xfffffffdffffffffffffffffffffffff
    model = ShortWeierstrassModel()
    coords = ShortWeierstrassModel().coordinates["projective"]
    return (EllipticCurve(model, coords, prime, dict(a=0xfffffffdfffffffffffffffffffffffc,
                                                     b=0xe87579c11079f43dd824993c2cee5ed3),
                          InfinityPoint(coords)),
            Point(coords, X=Mod(0x161ff7528b899b2d0c28607ca52c5b86, prime),
                  Y=Mod(0xcf5ac8395bafeb13c02da292dded7a83, prime),
                  Z=Mod(1, prime)))


def get_curve25519():
    prime = 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffed
    model = MontgomeryModel()
    coords = model.coordinates["xz"]
    return (EllipticCurve(model, coords, prime,
                          dict(a=486662, b=1),
                          InfinityPoint(coords)),
            Point(coords, X=Mod(9, prime), Z=Mod(1, prime)))
