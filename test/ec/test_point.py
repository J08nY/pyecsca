from unittest import TestCase

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.params import get_params
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel
from pyecsca.ec.point import Point, InfinityPoint
import pytest


class PointTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.base = self.secp128r1.generator
        self.coords = self.secp128r1.curve.coordinate_model
        self.affine = AffineCoordinateModel(ShortWeierstrassModel())


@pytest.fixture()
def coords(secp128r1):
    return secp128r1.curve.coordinate_model


@pytest.fixture()
def affine_model():
    return AffineCoordinateModel(ShortWeierstrassModel())


def test_construction(coords):
    with pytest.raises(ValueError):
        Point(coords)


def test_to_affine(secp128r1, coords, affine_model):
    pt = Point(
        coords,
        X=Mod(0x161FF7528B899B2D0C28607CA52C5B86, secp128r1.curve.prime),
        Y=Mod(0xCF5AC8395BAFEB13C02DA292DDED7A83, secp128r1.curve.prime),
        Z=Mod(1, secp128r1.curve.prime),
    )
    affine = pt.to_affine()

    assert isinstance(affine.coordinate_model, AffineCoordinateModel)
    assert set(affine.coords.keys()) == set(affine_model.variables)
    assert affine.coords["x"] == pt.coords["X"]
    assert affine.coords["y"] == pt.coords["Y"]
    assert affine.to_affine() == affine

    affine = InfinityPoint(coords).to_affine()
    assert isinstance(affine, InfinityPoint)


def test_to_model(secp128r1, coords, affine_model):
    affine = Point(
        affine_model,
        x=Mod(0xABCD, secp128r1.curve.prime),
        y=Mod(0xEF, secp128r1.curve.prime),
    )
    projective_model = coords
    other = affine.to_model(projective_model, secp128r1.curve)

    assert other.coordinate_model == projective_model
    assert set(other.coords.keys()) == set(projective_model.variables)
    assert other.coords["X"] == affine.coords["x"]
    assert other.coords["Y"] == affine.coords["y"]
    assert other.coords["Z"] == Mod(1, secp128r1.curve.prime)

    infty = InfinityPoint(AffineCoordinateModel(secp128r1.curve.model))
    other_infty = infty.to_model(coords, secp128r1.curve)
    assert isinstance(other_infty, InfinityPoint)

    with pytest.raises(ValueError):
        secp128r1.generator.to_model(coords, secp128r1.curve)


def test_to_from_affine(secp128r1, coords):
    pt = Point(
        coords,
        X=Mod(0x161FF7528B899B2D0C28607CA52C5B86, secp128r1.curve.prime),
        Y=Mod(0xCF5AC8395BAFEB13C02DA292DDED7A83, secp128r1.curve.prime),
        Z=Mod(1, secp128r1.curve.prime),
    )
    other = pt.to_affine().to_model(coords, secp128r1.curve)
    assert pt == other


def test_equals(secp128r1, coords):
    pt = Point(
        coords,
        X=Mod(0x4, secp128r1.curve.prime),
        Y=Mod(0x6, secp128r1.curve.prime),
        Z=Mod(2, secp128r1.curve.prime),
    )
    other = Point(
        coords,
        X=Mod(0x2, secp128r1.curve.prime),
        Y=Mod(0x3, secp128r1.curve.prime),
        Z=Mod(1, secp128r1.curve.prime),
    )
    third = Point(
        coords,
        X=Mod(0x5, secp128r1.curve.prime),
        Y=Mod(0x3, secp128r1.curve.prime),
        Z=Mod(1, secp128r1.curve.prime),
    )
    assert pt.equals(other)
    assert pt != other
    assert not pt.equals(2)  # type: ignore
    assert pt != 2
    assert not pt.equals(third)
    assert pt != third
    assert pt.equals_scaled(other)
    assert pt.equals_affine(other)
    assert not pt.equals_scaled(third)

    infty_one = InfinityPoint(coords)
    infty_other = InfinityPoint(coords)
    assert infty_one.equals(infty_other)
    assert infty_one.equals_affine(infty_other)
    assert infty_one.equals_scaled(infty_other)
    assert infty_one == infty_other
    assert not pt.equals(infty_one)
    assert not pt.equals_affine(infty_one)
    assert not pt.equals_scaled(infty_one)

    mont = MontgomeryModel()
    different = Point(
        mont.coordinates["xz"],
        X=Mod(
            0x64DACCD2656420216545E5F65221EB,
            0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
        ),
        Z=Mod(1, 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA),
    )
    assert not pt.equals(different)
    assert pt != different


def test_bytes(secp128r1, coords):
    pt = Point(
        coords,
        X=Mod(0x4, secp128r1.curve.prime),
        Y=Mod(0x6, secp128r1.curve.prime),
        Z=Mod(2, secp128r1.curve.prime),
    )
    assert bytes(pt) == \
           b"\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02"
    assert bytes(InfinityPoint(coords)) == b"\x00"


def test_iter(secp128r1, coords):
    pt = Point(
        coords,
        X=Mod(0x4, secp128r1.curve.prime),
        Y=Mod(0x6, secp128r1.curve.prime),
        Z=Mod(2, secp128r1.curve.prime),
    )
    t = tuple(pt)
    assert len(t) == 3
    assert len(pt) == 3
