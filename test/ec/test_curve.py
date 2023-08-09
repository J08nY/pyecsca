from binascii import unhexlify
import pytest

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.error import UnsatisfiedAssumptionError
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import MontgomeryModel
from pyecsca.ec.point import Point, InfinityPoint


def test_init(secp128r1):
    with pytest.raises(ValueError):
        EllipticCurve(
            MontgomeryModel(),
            secp128r1.curve.coordinate_model,
            1,
            InfinityPoint(secp128r1.curve.coordinate_model),
            parameters={},
        )

    with pytest.raises(ValueError):
        EllipticCurve(
            secp128r1.curve.model,
            secp128r1.curve.coordinate_model,
            15,
            InfinityPoint(secp128r1.curve.coordinate_model),
            parameters={"c": 0},
        )

    with pytest.raises(ValueError):
        EllipticCurve(
            secp128r1.curve.model,
            secp128r1.curve.coordinate_model,
            15,
            InfinityPoint(secp128r1.curve.coordinate_model),
            parameters={"a": Mod(1, 5), "b": Mod(2, 5)},
        )


def test_to_coords(secp128r1):
    affine = secp128r1.to_affine()
    m1_coords = affine.curve.model.coordinates["projective-1"]
    m3_coords = affine.curve.model.coordinates["projective-3"]
    with pytest.raises(UnsatisfiedAssumptionError):
        affine.to_coords(m1_coords)
    affine.to_coords(m3_coords)


def test_to_affine(secp128r1):
    affine = secp128r1.to_affine()
    model = AffineCoordinateModel(affine.curve.model)
    assert affine.curve.coordinate_model == model
    assert affine.generator.coordinate_model == model


def test_is_neutral(secp128r1):
    assert secp128r1.curve.is_neutral(
        InfinityPoint(secp128r1.curve.coordinate_model)
    )


def test_is_on_curve(secp128r1, curve25519):
    assert secp128r1.curve.is_on_curve(secp128r1.curve.neutral)
    pt = Point(
        secp128r1.curve.coordinate_model,
        X=Mod(0x161FF7528B899B2D0C28607CA52C5B86, secp128r1.curve.prime),
        Y=Mod(0xCF5AC8395BAFEB13C02DA292DDED7A83, secp128r1.curve.prime),
        Z=Mod(1, secp128r1.curve.prime),
    )
    assert secp128r1.curve.is_on_curve(pt)
    assert secp128r1.curve.is_on_curve(pt.to_affine())
    other = Point(
        secp128r1.curve.coordinate_model,
        X=Mod(0x161FF7528B899B2D0C28607CA52C5B86, secp128r1.curve.prime),
        Y=Mod(0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA, secp128r1.curve.prime),
        Z=Mod(1, secp128r1.curve.prime),
    )
    assert not secp128r1.curve.is_on_curve(other)
    assert not secp128r1.curve.is_on_curve(curve25519.generator)


def test_affine_add(secp128r1):
    pt = Point(
        AffineCoordinateModel(secp128r1.curve.model),
        x=Mod(0xEB916224EDA4FB356421773573297C15, secp128r1.curve.prime),
        y=Mod(0xBCDAF32A2C08FD4271228FEF35070848, secp128r1.curve.prime),
    )
    affine_base = secp128r1.generator.to_affine()
    assert secp128r1.curve.affine_add(affine_base, pt) is not None

    added = secp128r1.curve.affine_add(affine_base, affine_base)
    doubled = secp128r1.curve.affine_double(affine_base)
    assert added == doubled
    assert secp128r1.curve.affine_add(secp128r1.curve.neutral, pt) == pt
    assert secp128r1.curve.affine_add(pt, secp128r1.curve.neutral) == pt


def test_affine_double(secp128r1):
    affine_base = secp128r1.generator.to_affine()
    assert secp128r1.curve.affine_double(affine_base) is not None
    assert secp128r1.curve.affine_double(secp128r1.curve.neutral) == \
           secp128r1.curve.neutral


def test_affine_negate(secp128r1, curve25519):
    affine_base = secp128r1.generator.to_affine()
    assert secp128r1.curve.affine_negate(affine_base) is not None
    assert secp128r1.curve.affine_negate(secp128r1.curve.neutral) == \
           secp128r1.curve.neutral
    with pytest.raises(ValueError):
        secp128r1.curve.affine_negate(secp128r1.generator)
    with pytest.raises(ValueError):
        secp128r1.curve.affine_negate(curve25519.generator)


def test_affine_multiply(secp128r1, curve25519):
    affine_base = secp128r1.generator.to_affine()
    expected = affine_base
    expected = secp128r1.curve.affine_double(expected)
    expected = secp128r1.curve.affine_double(expected)
    expected = secp128r1.curve.affine_add(expected, affine_base)
    expected = secp128r1.curve.affine_double(expected)
    assert secp128r1.curve.affine_multiply(affine_base, 10) == expected
    assert secp128r1.curve.affine_multiply(secp128r1.curve.neutral, 10) == \
           secp128r1.curve.neutral
    with pytest.raises(ValueError):
        secp128r1.curve.affine_multiply(secp128r1.generator, 10)
    with pytest.raises(ValueError):
        secp128r1.curve.affine_multiply(curve25519.generator, 10)


def test_affine_neutral(secp128r1, curve25519, ed25519):
    assert secp128r1.curve.affine_neutral is None
    assert curve25519.curve.affine_neutral is None
    assert ed25519.curve.affine_neutral is not None


def test_neutral_is_affine(secp128r1, curve25519, ed25519):
    assert not secp128r1.curve.neutral_is_affine
    assert not curve25519.curve.neutral_is_affine
    assert ed25519.curve.neutral_is_affine


@pytest.mark.parametrize("curve_name", ["secp128r1", "curve25519", "ed25519"])
def test_affine_random(curve_name, request):
    params = request.getfixturevalue(curve_name)
    for _ in range(20):
        pt = params.curve.affine_random()
        assert pt is not None
        assert params.curve.is_on_curve(pt)


def test_eq(secp128r1, curve25519):
    assert secp128r1.curve == secp128r1.curve
    assert secp128r1.curve != curve25519.curve
    assert secp128r1.curve is not None


def test_decode(secp128r1):
    affine_curve = secp128r1.curve.to_affine()
    affine_point = secp128r1.generator.to_affine()
    decoded = affine_curve.decode_point(bytes(affine_point))
    assert decoded == affine_point

    affine_compressed_bytes = unhexlify("03161ff7528b899b2d0c28607ca52c5b86")
    decoded_compressed = affine_curve.decode_point(affine_compressed_bytes)
    assert decoded_compressed == affine_point
    affine_compressed_bytes = unhexlify("02161ff7528b899b2d0c28607ca52c5b86")
    decoded_compressed = affine_curve.decode_point(affine_compressed_bytes)
    decoded_compressed = secp128r1.curve.affine_negate(decoded_compressed)
    assert decoded_compressed == affine_point

    infinity_bytes = unhexlify("00")
    decoded_infinity = affine_curve.decode_point(infinity_bytes)
    assert affine_curve.neutral == decoded_infinity

    with pytest.raises(ValueError):
        affine_curve.decode_point(unhexlify("03161ff7528b899b2d0c28607ca52c5b"))
    with pytest.raises(ValueError):
        affine_curve.decode_point(
            unhexlify("04161ff7528b899b2d0c28607ca52c5b2c5b2c5b2c5b")
        )
    with pytest.raises(ValueError):
        affine_curve.decode_point(unhexlify("7a161ff7528b899b2d0c28607ca52c5b86"))
    with pytest.raises(ValueError):
        affine_curve.decode_point(unhexlify("03161ff7528b899b2d0c28607ca52c5b88"))
