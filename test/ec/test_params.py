import pickle

from importlib_resources import files, as_file

import pytest

import test.data.ec
from pyecsca.ec.mod import Mod
from pyecsca.ec.point import Point, InfinityPoint
from pyecsca.misc.cfg import TemporaryConfig
from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.error import UnsatisfiedAssumptionError
from pyecsca.ec.params import get_params, load_params, load_category, get_category, DomainParameters, \
    load_params_ectester, load_params_ecgen
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.curve import EllipticCurve


def test_eq(secp128r1, curve25519):
    assert secp128r1.__eq__(secp128r1)
    assert secp128r1 != curve25519
    assert secp128r1 is not None


def test_str(secp128r1):
    assert str(secp128r1) == "DomainParameters(secg/secp128r1)"


@pytest.mark.parametrize("name,coords",
                         [
                             ("secg/secp128r1", "projective"),
                             ("secg/secp256r1", "projective"),
                             ("secg/secp521r1", "projective"),
                             ("other/Curve25519", "xz"),
                             ("other/Ed25519", "projective"),
                             ("other/Ed448", "projective"),
                             ("other/E-222", "projective"),
                         ])
def test_get_params(name, coords):
    params = get_params(*name.split("/"), coords)
    try:
        assert params.curve.is_on_curve(params.generator)
    except NotImplementedError:
        pass


@pytest.mark.parametrize("name,coords",
                         [
                             ("anssi", "projective"),
                             (
                                     "brainpool",
                                     lambda name: "projective" if name.endswith("r1") else "jacobian",
                             ),
                         ])
def test_get_category(name, coords):
    get_category(name, coords)


def test_load_params():
    with as_file(files(test.data.ec).joinpath("curve.json")) as path:
        params = load_params(path, "projective")
        try:
            assert params.curve.is_on_curve(params.generator)
        except NotImplementedError:
            pass


def test_load_params_ectester(secp128r1):
    with as_file(files(test.data.ec).joinpath("ectester_secp128r1.csv")) as path:
        params = load_params_ectester(path, "projective")
        assert params.curve.is_on_curve(params.generator)
        assert params == secp128r1


def test_load_params_ecgen(secp128r1):
    with as_file(files(test.data.ec).joinpath("ecgen_secp128r1.json")) as path:
        params = load_params_ecgen(path, "projective")
        assert params.curve.is_on_curve(params.generator)
        assert params == secp128r1


def test_load_category():
    with as_file(files(test.data.ec).joinpath("curves.json")) as path:
        category = load_category(path, "yz")
        assert len(category) == 1


@pytest.mark.parametrize("name,coords",
                         [
                             ("no_category/some", "else"),
                             ("secg/no_curve", "else"),
                             ("secg/secp128r1", "some"),
                         ])
def test_unknown(name, coords):
    with pytest.raises(ValueError):
        get_params(*name.split("/"), coords)


def test_assumption():
    with pytest.raises(UnsatisfiedAssumptionError):
        get_params("secg", "secp128r1", "projective-1")
    with TemporaryConfig() as cfg:
        cfg.ec.unsatisfied_coordinate_assumption_action = "ignore"
        params = get_params("secg", "secp128r1", "projective-1")
        assert params is not None
    assert get_params("secg", "secp128r1", "projective-3") is not None


def test_infty():
    with pytest.raises(ValueError):
        get_params("other", "Ed25519", "modified", False)
    assert get_params("secg", "secp128r1", "projective", False) is not None


def test_no_binary():
    with pytest.raises(ValueError):
        get_params("secg", "sect163r1", "something")


def test_no_extension():
    with pytest.raises(ValueError):
        get_params("other", "Fp254n2BNa", "something")


def test_affine():
    aff = get_params("secg", "secp128r1", "affine")
    assert isinstance(aff.curve.coordinate_model, AffineCoordinateModel)


def test_custom_params():
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    p = 0xd7d1247f
    a = Mod(0xa4a44016, p)
    b = Mod(0x73f76716, p)
    n = 0xd7d2a475
    h = 1
    gx, gy, gz = Mod(0x54eed6d7, p), Mod(0x6f1e55ac, p), Mod(1, p)
    generator = Point(coords, X=gx, Y=gy, Z=gz)
    neutral = InfinityPoint(coords)

    curve = EllipticCurve(model, coords, p, neutral, {"a": a, "b": b})
    params = DomainParameters(curve, generator, n, h)
    assert params is not None
    res = params.curve.affine_double(generator.to_affine())
    assert res is not None


def test_pickle(secp128r1):
    assert secp128r1 == pickle.loads(pickle.dumps(secp128r1))
