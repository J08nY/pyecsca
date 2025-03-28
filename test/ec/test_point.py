import pickle
from contextlib import nullcontext as does_not_raise

import pytest

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.mod import mod
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel
from pyecsca.ec.params import get_params
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.ec.error import UnsatisfiedAssumptionError


@pytest.fixture()
def secp128r1_coords(secp128r1):
    return secp128r1.curve.coordinate_model


@pytest.fixture()
def affine_model():
    return AffineCoordinateModel(ShortWeierstrassModel())


def test_construction(secp128r1_coords):
    with pytest.raises(ValueError):
        Point(secp128r1_coords)
    with pytest.raises(ValueError):
        Point(secp128r1_coords, X=mod(1, 3), Y=mod(2, 7), Z=mod(1, 3))


def test_to_affine(secp128r1, secp128r1_coords, affine_model):
    pt = Point(
        secp128r1_coords,
        X=mod(0x161FF7528B899B2D0C28607CA52C5B86, secp128r1.curve.prime),
        Y=mod(0xCF5AC8395BAFEB13C02DA292DDED7A83, secp128r1.curve.prime),
        Z=mod(1, secp128r1.curve.prime),
    )
    affine = pt.to_affine()

    assert isinstance(affine.coordinate_model, AffineCoordinateModel)
    assert set(affine.coords.keys()) == set(affine_model.variables)
    assert affine.coords["x"] == pt.coords["X"]
    assert affine.coords["y"] == pt.coords["Y"]
    assert affine.to_affine() == affine

    affine = InfinityPoint(secp128r1_coords).to_affine()
    assert isinstance(affine, InfinityPoint)

    secp128r1_xz = get_params("secg", "secp128r1", "xz")
    with pytest.raises(NotImplementedError):
        secp128r1_xz.generator.to_affine()

    secp128r1_modified = get_params("secg", "secp128r1", "modified")
    modified = secp128r1_modified.generator.to_affine()
    assert modified is not None


def test_to_model(secp128r1, secp128r1_coords, affine_model):
    affine = Point(
        affine_model,
        x=mod(0xABCD, secp128r1.curve.prime),
        y=mod(0xEF, secp128r1.curve.prime),
    )
    other = affine.to_model(secp128r1_coords, secp128r1.curve)

    assert other.coordinate_model == secp128r1_coords
    assert set(other.coords.keys()) == set(secp128r1_coords.variables)
    assert other.coords["X"] == affine.coords["x"]
    assert other.coords["Y"] == affine.coords["y"]
    assert other.coords["Z"] == mod(1, secp128r1.curve.prime)

    infty = InfinityPoint(AffineCoordinateModel(secp128r1.curve.model))
    other_infty = infty.to_model(secp128r1_coords, secp128r1.curve)
    assert isinstance(other_infty, InfinityPoint)

    with pytest.raises(ValueError):
        secp128r1.generator.to_model(secp128r1_coords, secp128r1.curve)


@pytest.mark.parametrize("category,curve,coords,raises", [
    ("secg", "secp128r1", "projective", does_not_raise()),
    ("secg", "secp128r1", "jacobian", does_not_raise()),
    ("secg", "secp128r1", "modified", does_not_raise()),
    ("secg", "secp128r1", "xyzz", does_not_raise()),
    ("secg", "secp128r1", "xz", pytest.raises(NotImplementedError)),    # Not really possible
    ("other", "Curve25519", "xz", pytest.raises(NotImplementedError)),  # Not really possible
    ("other", "E-222", "inverted", does_not_raise()),
    ("other", "E-222", "projective", does_not_raise()),
    # ("other", "E-222", "yz", does_not_raise()),         # No STD curve satisfies this formula assumption
    # ("other", "E-222", "yzsquared", does_not_raise()),  # No STD curve satisfies this formula assumption
    ("other", "Ed25519", "extended", does_not_raise()),
    ("other", "Ed25519", "inverted", does_not_raise()),
    ("other", "Ed25519", "projective", does_not_raise()),
])
def test_to_from_affine(category, curve, coords, raises):
    params = get_params(category, curve, coords)
    with raises:
        other = params.generator.to_affine().to_model(params.curve.coordinate_model, params.curve)
        assert params.generator == other
        random_affine = params.curve.affine_random()
        assert random_affine.to_model(params.curve.coordinate_model, params.curve).to_affine() == random_affine


def test_equals(secp128r1, secp128r1_coords):
    pt = Point(
        secp128r1_coords,
        X=mod(0x4, secp128r1.curve.prime),
        Y=mod(0x6, secp128r1.curve.prime),
        Z=mod(2, secp128r1.curve.prime),
    )
    other = Point(
        secp128r1_coords,
        X=mod(0x2, secp128r1.curve.prime),
        Y=mod(0x3, secp128r1.curve.prime),
        Z=mod(1, secp128r1.curve.prime),
    )
    third = Point(
        secp128r1_coords,
        X=mod(0x5, secp128r1.curve.prime),
        Y=mod(0x3, secp128r1.curve.prime),
        Z=mod(1, secp128r1.curve.prime),
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

    assert pt.equals_homog(pt)
    assert pt.equals_homog(other)
    assert other.equals_homog(pt)
    assert not pt.equals_homog(third)
    assert not third.equals_homog(pt)

    infty_one = InfinityPoint(secp128r1_coords)
    infty_other = InfinityPoint(secp128r1_coords)
    assert infty_one.equals(infty_other)
    assert infty_one.equals_affine(infty_other)
    assert infty_one.equals_scaled(infty_other)
    assert infty_one.equals_homog(infty_other)
    assert infty_one == infty_other
    assert not pt.equals(infty_one)
    assert not pt.equals_affine(infty_one)
    assert not pt.equals_scaled(infty_one)
    assert not pt.equals_homog(infty_one)

    mont = MontgomeryModel()
    different = Point(
        mont.coordinates["xz"],
        X=mod(
            0x64DACCD2656420216545E5F65221EB,
            0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
        ),
        Z=mod(1, 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA),
    )
    assert not pt.equals(different)
    assert pt != different


def test_homog():
    model = ShortWeierstrassModel()
    for coords_name, coords in model.coordinates.items():
        try:
            params = get_params("secg", "secp128r1", coords_name, infty=False)
        except UnsatisfiedAssumptionError:
            continue
        infty = params.curve.neutral
        rand_aff = params.curve.affine_random()
        one1 = rand_aff.to_model(coords, params.curve)
        one2 = rand_aff.to_model(coords, params.curve, randomized=True)
        one3 = rand_aff.to_model(coords, params.curve, randomized=True)
        assert one1.equals_homog(one2)
        assert one1.equals_homog(one3)
        assert one2.equals_homog(one3)
        assert not one1.equals_homog(infty)
        assert infty.equals_homog(infty)
        while True:
            other_aff = params.curve.affine_random()
            if other_aff != rand_aff:
                break
        other = other_aff.to_model(coords, params.curve)
        assert not one1.equals_homog(other)
        assert not one2.equals_homog(other)
        assert not one3.equals_homog(other)


def test_bytes(secp128r1, secp128r1_coords):
    pt = Point(
        secp128r1_coords,
        X=mod(0x4, secp128r1.curve.prime),
        Y=mod(0x6, secp128r1.curve.prime),
        Z=mod(2, secp128r1.curve.prime),
    )
    assert bytes(pt) == \
           b"\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02"
    assert bytes(InfinityPoint(secp128r1_coords)) == b"\x00"


def test_iter(secp128r1, secp128r1_coords):
    pt = Point(
        secp128r1_coords,
        X=mod(0x4, secp128r1.curve.prime),
        Y=mod(0x6, secp128r1.curve.prime),
        Z=mod(2, secp128r1.curve.prime),
    )
    t = tuple(pt)
    assert len(t) == 3
    assert len(pt) == 3

    assert len(InfinityPoint(secp128r1_coords)) == 0
    assert len(tuple(InfinityPoint(secp128r1_coords))) == 0


def test_pickle(secp128r1, secp128r1_coords):
    pt = Point(
        secp128r1_coords,
        X=mod(0x4, secp128r1.curve.prime),
        Y=mod(0x6, secp128r1.curve.prime),
        Z=mod(2, secp128r1.curve.prime),
    )
    pickle.dumps(secp128r1_coords)
    assert pt == pickle.loads(pickle.dumps(pt))
