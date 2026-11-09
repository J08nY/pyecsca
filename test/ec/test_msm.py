import pytest

from pyecsca.ec.mult import (
    AccumulationOrder,
    MultiScalarMultiplier,
    ScalarMultiplier,
)
from pyecsca.ec.context import DefaultContext, local
from pyecsca.ec.mult.msm import PippengerMultiplier, MultiScalarMultiplierAction
from pyecsca.ec.error import NonInvertibleError
from pyecsca.ec.point import InfinityPoint, Point


def make_points(params, multipliers):
    """Build a list of distinct projective points as multiples of the generator."""
    G_affine = params.generator.to_affine()
    return [
        params.curve.affine_multiply(G_affine, m).to_model(
            params.curve.coordinate_model, params.curve
        )
        for m in multipliers
    ]


def assert_pt_equality(one: Point, other: Point, scale):
    if scale:
        assert one == other
    else:
        assert one.equals(other)


def complete_affine_sum(curve, terms):
    """
    Sum affine points, handling doubling and cancellation explicitly.

    ``affine_add`` handles the identity and the doubling case but not the
    cancellation case (``P + (-P)``), so it is completed here to serve as a
    reference for inputs that contain a negation pair.
    """
    total = None  # the identity
    for term in terms:
        if term is None:
            continue
        if total is None:
            total = term
        elif total.x == term.x:
            total = curve.affine_double(total) if total.y == term.y else None
        else:
            total = curve.affine_add(total, term)
    return total


def msm_reference_point(params, points, scalars):
    """The reference multi-scalar product as a point in the parameters' coordinate model."""
    curve = params.curve
    terms = [
        curve.affine_multiply(point.to_affine(), scalar)
        for point, scalar in zip(points, scalars)
        if scalar != 0
    ]
    total = complete_affine_sum(curve, terms)
    if total is None:
        return curve.neutral
    return total.to_model(curve.coordinate_model, curve)


def get_formulas(secp128r1, scale):
    coords = secp128r1.curve.coordinate_model
    add = coords.formulas["add-2015-rcb"]
    dbl = coords.formulas["dbl-2015-rcb"]
    scl = coords.formulas[scale] if scale is not None else None
    return add, dbl, scl


@pytest.mark.parametrize("width", [1, 2, 3, 5])
@pytest.mark.parametrize(
    "accumulation_order", tuple(AccumulationOrder), ids=lambda o: o.name
)
@pytest.mark.parametrize("complete", [True, False], ids=["complete", ""])
@pytest.mark.parametrize("skip_zero", [True, False], ids=["skip-zero", ""])
@pytest.mark.parametrize("scale", ["z", None], ids=["scaled", ""])
def test_pippenger(secp128r1, width, accumulation_order, complete, skip_zero, scale):
    add, dbl, scl = get_formulas(secp128r1, scale)
    points = make_points(secp128r1, [7, 13, 101, 555])
    scalars = [257, 997, 42424, 0]

    mult = PippengerMultiplier(
        add,
        dbl,
        width,
        scl=scl,
        accumulation_order=accumulation_order,
        complete=complete,
        skip_zero=skip_zero
    )
    mult.init(secp128r1, points)
    res = mult.multiply(scalars)
    ref = msm_reference_point(secp128r1, points, scalars)
    assert_pt_equality(res, ref, scale is not None)

    # A single point with width >= 2 forces the running sum to add a point to itself.
    mult.init(secp128r1, points[:1])
    res = mult.multiply([0x123456789])
    ref = msm_reference_point(secp128r1, points[:1], [0x123456789])
    assert_pt_equality(res, ref, scale is not None)


@pytest.mark.parametrize("width", [1, 2, 3, 5])
@pytest.mark.parametrize(
    "accumulation_order", tuple(AccumulationOrder), ids=lambda o: o.name
)
@pytest.mark.parametrize("complete", [True, False], ids=["complete", ""])
@pytest.mark.parametrize("skip_zero", [True, False], ids=["skip-zero", ""])
@pytest.mark.parametrize("scale", ["z", None], ids=["scaled", ""])
def test_pippenger_negations(secp128r1, width, accumulation_order, complete, skip_zero, scale):
    """Base points that are the negation of one another.

    The bucket accumulation then adds a point to its own negation (a
    cancellation to the point at infinity) when the two land in the same window.
    """
    add, dbl, scl = get_formulas(secp128r1, scale)
    coords = secp128r1.curve.coordinate_model
    G_affine = secp128r1.generator.to_affine()
    curve = secp128r1.curve
    P = curve.affine_multiply(G_affine, 7).to_model(coords, curve)
    N = curve.affine_negate(P.to_affine()).to_model(coords, curve)
    D = curve.affine_multiply(G_affine, 13).to_model(coords, curve)
    # Sanity: N is the negation of P (so P + N is the point at infinity).
    assert not P.equals_affine(N)
    assert P.equals(curve.affine_negate(N.to_affine()).to_model(coords, curve))

    def is_projective_infinity(point):
        # The incomplete projective formulas represent the point at infinity as
        # Z == 0, which is not an InfinityPoint instance and is not == to it.
        return (not isinstance(point, InfinityPoint)) and point.Z == 0

    # Scenarios that do not cancel to the point at infinity; compare against the
    # affine reference (a regular point).
    scenarios = [
        ([P, N], [258, 257]),        # partial: P
        ([P, N], [257, 0]),          # only P
        ([P, N], [0, 257]),          # only -P
        ([P, N, D], [41, 41, 5]),    # P + (-P) cancels, leaving 5*D
        ([P, N, D], [41, 42, 5]),    # leaves P + 5*D
        ([P, N, D], [0, 41, 5]),     # -41*P + 5*D
        ([P, N, D], [1, 1, 1]),      # all unit scalars
        ([P, N, D], [3, 3, 3]),
        ([P, N, D], [0xFFFFFFFF, 0xFFFFFFF, 7]),  # oversized, near cancellation
    ]
    for points, scalars in scenarios:
        mult = PippengerMultiplier(
            add,
            dbl,
            width,
            scl=scl,
            accumulation_order=accumulation_order,
            complete=complete,
            skip_zero=skip_zero
        )
        mult.init(secp128r1, points)
        res = mult.multiply(scalars)
        ref = msm_reference_point(secp128r1, points, scalars)
        assert not is_projective_infinity(res)
        assert res.equals(ref), (points, scalars, width, accumulation_order, complete, scale)

    # Scenarios that cancel to the point at infinity.
    infinity_scenarios = [
        ([P, N], [257, 257]),        # 257*P + 257*(-P) = O
        ([P, N], [0x21F, 0x21F]),
        ([P, N, D], [41, 41, 0]),    # P + (-P) cancels
        ([P, N, D], [0xFFFFFFFF, 0xFFFFFFFF, 0]),
    ]
    for points, scalars in infinity_scenarios:
        mult = PippengerMultiplier(
            add,
            dbl,
            width,
            scl=scl,
            accumulation_order=accumulation_order,
            complete=complete,
            skip_zero=skip_zero
        )
        mult.init(secp128r1, points)
        if scl is not None:
            # The scaling formula cannot handle the point at infinity.
            with pytest.raises(NonInvertibleError):
                mult.multiply(scalars)
        else:
            res = mult.multiply(scalars)
            assert is_projective_infinity(res), (
                points, scalars, width, accumulation_order, complete, scale
            )


@pytest.mark.parametrize("width", [1, 3])
def test_pippenger_zero(secp128r1, width):
    add, dbl, _ = get_formulas(secp128r1, None)
    points = make_points(secp128r1, [7, 13, 101])
    mult = PippengerMultiplier(add, dbl, width)
    mult.init(secp128r1, points)
    assert secp128r1.curve.neutral == mult.multiply([0, 0, 0])
    # A zero scalar must not contribute, but must still align with the others.
    res = mult.multiply([0, 997, 0])
    ref = msm_reference_point(secp128r1, points, [0, 997, 0])
    assert res.equals(ref)


def test_pippenger_empty(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    mult = PippengerMultiplier(add, dbl, 3)
    mult.init(secp128r1, [])
    assert secp128r1.curve.neutral == mult.multiply([])


def test_pippenger_scalars_mismatch(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    points = make_points(secp128r1, [7, 13])
    mult = PippengerMultiplier(add, dbl, 3)
    mult.init(secp128r1, points)
    with pytest.raises(ValueError):
        mult.multiply([1, 2, 3])


def test_pippenger_not_initialized(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    mult = PippengerMultiplier(add, dbl, 3)
    with pytest.raises(ValueError):
        mult.multiply([1, 2])


def test_pippenger_init_fail(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    points = make_points(secp128r1, [7, 13])
    mult = PippengerMultiplier(add, dbl, 3)
    # A point in a different coordinate model is rejected.
    affine_point = secp128r1.generator.to_affine()
    with pytest.raises(ValueError):
        mult.init(secp128r1, [affine_point, points[1]])


def test_pippenger_is_not_scalar_multiplier(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    mult = PippengerMultiplier(add, dbl, 3)
    assert isinstance(mult, MultiScalarMultiplier)
    assert not isinstance(mult, ScalarMultiplier)


def test_pippenger_repr_hash_eq(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    m1 = PippengerMultiplier(add, dbl, 3)
    m2 = PippengerMultiplier(add, dbl, 3)
    m3 = PippengerMultiplier(add, dbl, 4)
    assert m1 == m2
    assert hash(m1) == hash(m2)
    assert m1 != m3
    assert "PippengerMultiplier" in repr(m1)


def test_pippenger_invalid_width(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    with pytest.raises(ValueError):
        PippengerMultiplier(add, dbl, 0)


def test_context(secp128r1):
    add, dbl, _ = get_formulas(secp128r1, None)
    points = make_points(secp128r1, [7, 13])
    scalars = [1, 2]
    mult = PippengerMultiplier(add, dbl, 3)
    with local(DefaultContext()) as ctx:
        mult.init(secp128r1, points)
        result = mult.multiply(scalars)
        action = ctx.actions[0].action
    assert isinstance(action, MultiScalarMultiplierAction)
    assert result == action.result
    assert points == action.points
    assert scalars == action.scalars
