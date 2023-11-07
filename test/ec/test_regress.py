from typing import cast

import pytest
from sympy import symbols

from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.error import UnsatisfiedAssumptionError
from pyecsca.ec.formula import AdditionFormula, DoublingFormula, ScalingFormula
from pyecsca.ec.mod import Mod, SymbolicMod
from pyecsca.ec.model import MontgomeryModel, EdwardsModel
from pyecsca.ec.params import get_params
from pyecsca.ec.mult import LTRMultiplier
from pyecsca.ec.point import Point, InfinityPoint


def test_issue_7():
    secp128r1 = get_params("secg", "secp128r1", "projective")
    base = secp128r1.generator
    coords = secp128r1.curve.coordinate_model
    add = cast(AdditionFormula, coords.formulas["add-1998-cmo"])
    dbl = cast(DoublingFormula, coords.formulas["dbl-1998-cmo"])
    scl = cast(ScalingFormula, coords.formulas["z"])
    mult = LTRMultiplier(add, dbl, scl, always=False, complete=False, short_circuit=True)
    mult.init(secp128r1, base)
    pt = mult.multiply(13613624287328732)
    assert isinstance(pt.coords["X"], Mod)
    assert isinstance(pt.coords["Y"], Mod)
    assert isinstance(pt.coords["Z"], Mod)
    mult.init(secp128r1, pt)
    a = mult.multiply(1)
    assert not isinstance(a.coords["X"].x, float)
    assert not isinstance(a.coords["Y"].x, float)
    assert not isinstance(a.coords["Z"].x, float)


def test_issue_8():
    e222 = get_params("other", "E-222", "projective")
    base = e222.generator
    affine_base = base.to_affine()
    affine_double = e222.curve.affine_double(affine_base)
    affine_triple = e222.curve.affine_add(affine_base, affine_double)
    assert affine_double is not None
    assert affine_triple is not None


def test_issue_9():
    model = MontgomeryModel()
    coords = model.coordinates["xz"]
    p = 19
    neutral = Point(coords, X=Mod(1, p), Z=Mod(0, p))
    curve = EllipticCurve(model, coords, p, neutral, {"a": Mod(8, p), "b": Mod(1, p)})
    base = Point(coords, X=Mod(12, p), Z=Mod(1, p))
    formula = coords.formulas["dbl-1987-m-2"]
    res = formula(p, base, **curve.parameters)[0]
    assert res is not None
    affine_base = Point(AffineCoordinateModel(model), x=Mod(12, p), y=Mod(2, p))
    dbase = curve.affine_double(affine_base).to_model(coords, curve)
    ladder = coords.formulas["ladd-1987-m-3"]
    one, other = ladder(p, base, dbase, base, **curve.parameters)
    assert one is not None
    assert other is not None


def test_issue_10():
    model = EdwardsModel()
    coords = model.coordinates["yz"]
    coords_sqr = model.coordinates["yzsquared"]
    p = 0x1D
    c = Mod(1, p)
    d = Mod(0x1C, p)
    r = d.sqrt()
    neutral = Point(coords, Y=c * r, Z=Mod(1, p))
    curve = EllipticCurve(model, coords, p, neutral, {"c": c, "d": d, "r": r})
    neutral_affine = Point(AffineCoordinateModel(model), x=Mod(0, p), y=c)
    assert neutral == neutral_affine.to_model(coords, curve)
    neutral_sqr = Point(coords_sqr, Y=c ** 2 * r, Z=Mod(1, p))
    assert neutral_sqr == neutral_affine.to_model(coords_sqr, curve)


def test_issue_13():
    model = EdwardsModel()
    coords = model.coordinates["yz"]
    c, r, d = symbols("c r d")
    p = 53
    c = SymbolicMod(c, p)
    r = SymbolicMod(r, p)
    d = SymbolicMod(d, p)
    yd, zd, yp, zp, yq, zq = symbols("yd zd yp zp yq zq")
    PmQ = Point(coords, Y=SymbolicMod(yd, p), Z=SymbolicMod(zd, p))
    P = Point(coords, Y=SymbolicMod(yp, p), Z=SymbolicMod(zp, p))
    Q = Point(coords, Y=SymbolicMod(yq, p), Z=SymbolicMod(zq, p))
    formula = coords.formulas["dadd-2006-g-2"]
    formula(p, PmQ, P, Q, c=c, r=r, d=d)


def test_issue_14():
    model = EdwardsModel()
    coords = model.coordinates["projective"]
    affine = AffineCoordinateModel(model)
    formula = coords.formulas["add-2007-bl-4"]

    with pytest.raises(UnsatisfiedAssumptionError):
        # p is 3 mod 4, so there is no square root of -1
        p = 19
        c = Mod(2, p)
        d = Mod(10, p)
        curve = EllipticCurve(model, coords, p, InfinityPoint(coords), {"c": c, "d": d})
        Paff = Point(affine, x=Mod(0xD, p), y=Mod(0x9, p))
        P = Paff.to_model(coords, curve)
        Qaff = Point(affine, x=Mod(0x4, p), y=Mod(0x12, p))
        Q = Qaff.to_model(coords, curve)
        formula(p, P, Q, **curve.parameters)[0]

    # p is 1 mod 4, so there is a square root of -1
    p = 29
    c = Mod(2, p)
    d = Mod(10, p)
    curve = EllipticCurve(model, coords, p, InfinityPoint(coords), {"c": c, "d": d})
    Paff = Point(affine, x=Mod(0xD, p), y=Mod(0x9, p))
    P = Paff.to_model(coords, curve)
    Qaff = Point(affine, x=Mod(0x4, p), y=Mod(0x12, p))
    Q = Qaff.to_model(coords, curve)
    PQaff = curve.affine_add(Paff, Qaff)
    R = formula(p, P, Q, **curve.parameters)[0]
    Raff = R.to_affine()
    assert PQaff == Raff


def test_issue_53():
    secp128r1 = get_params("secg", "secp128r1", "jacobian")
    coords = secp128r1.curve.coordinate_model
    formula = coords.formulas["dbl-1998-hnm"]
    formula(secp128r1.curve.prime, secp128r1.generator, **secp128r1.curve.parameters)
