import random
from functools import partial

import pytest

from pyecsca.ec.coordinates import EFDCoordinateModel
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.params import Point, InfinityPoint
from pyecsca.ec.mult import *
from pyecsca.sca.re.rpa import multiple_graph, multiples_from_graph
from pyecsca.sca.re.epa import errors_out, graph_to_check_inputs, graph_plot


def test_errors_out(secp128r1):
    precomp_ctx, full_ctx, out = multiple_graph(
        scalar=15,
        params=secp128r1,
        mult_class=LTRMultiplier,
        mult_factory=LTRMultiplier,
    )
    res_empty_checks = errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert not res_empty_checks

    def add_check(k, l):  # noqa
        return k == 6

    res_check_k_add = errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"add": add_check},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert res_check_k_add

    def affine_check(k):
        return k == 15

    res_check_k_affine = errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"affine": affine_check},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert res_check_k_affine


def test_errors_out_comb(secp128r1):
    precomp_ctx, full_ctx, out = multiple_graph(
        scalar=15,
        params=secp128r1,
        mult_class=CombMultiplier,
        mult_factory=partial(CombMultiplier, width=2),
    )

    def affine_check_comb(k):
        return k == 2**64

    res_check_k_affine_precomp = errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"affine": affine_check_comb},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert res_check_k_affine_precomp

    res_check_k_no_affine_precomp = errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"affine": affine_check_comb},
        check_condition="all",
        precomp_to_affine=False,
    )
    assert not res_check_k_no_affine_precomp


@pytest.mark.skip(reason="Debug only")
def test_memory_consumption(secp128r1):
    precomp_ctx, full_ctx, out = multiple_graph(
        scalar=2**127 + 12127486321,
        params=secp128r1,
        mult_class=LTRMultiplier,
        mult_factory=LTRMultiplier,
    )
    try:
        from pympler.asizeof import Asizer

        sizer = Asizer()
        sizer.exclude_types(EFDCoordinateModel)
        print(sizer.asized(precomp_ctx, detail=2).format())
        print(sizer.asized(full_ctx, detail=2).format())
        print(sizer.asized(out, detail=2).format())
    except ImportError:
        pass


def test_errors_out_precomp(secp128r1):
    precomp_ctx, full_ctx, out = multiple_graph(
        scalar=15,
        params=secp128r1,
        mult_class=WindowNAFMultiplier,
        mult_factory=partial(
            WindowNAFMultiplier, width=3, complete=False, precompute_negation=True
        ),
    )

    affine_multiples = []

    def affine_check(k):
        affine_multiples.append(k)
        return False

    add_multiples = []

    def add_check(k, l):  # noqa
        add_multiples.append((k, l))
        return False

    # Here we check "all" but only during the precomp.
    errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"affine": affine_check, "add": add_check},
        check_condition="all",
        precomp_to_affine=True,
        use_init=True,
        use_multiply=False,
    )
    assert set(affine_multiples) == set(precomp_ctx.precomp.keys())
    assert set(add_multiples) == {(1, 2)}

    # Here we check all, during both precomp and final multiply.
    affine_multiples = []
    add_multiples = []

    errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"affine": affine_check, "add": add_check},
        check_condition="all",
        precomp_to_affine=True,
        use_init=True,
        use_multiply=True,
    )
    # There should be all of the results of the precomp, plus the final multiply result.
    assert set(affine_multiples) == set(precomp_ctx.precomp.keys()) | {
        full_ctx.points[out]
    }
    # The add multiples should be the same as before, plus any inputs to add that happened
    # during the final multiply, there is only one, rest are doubles.
    assert set(add_multiples) == {(1, 2), (16, -1)}

    # Now check just the multiply with all.
    affine_multiples = []
    add_multiples = []

    errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"affine": affine_check, "add": add_check},
        check_condition="all",
        precomp_to_affine=True,
        use_init=False,
        use_multiply=True,
    )
    # Only the final result should be converted to affine, because we ignore precomp.
    assert set(affine_multiples) == {full_ctx.points[out]}
    # Only the single add in the multiply should be checked.
    assert set(add_multiples) == {(16, -1)}

    # Now check just the multiply with necessary only.
    affine_multiples = []
    add_multiples = []

    errors_out(
        precomp_ctx,
        full_ctx,
        out,
        check_funcs={"affine": affine_check, "add": add_check},
        check_condition="necessary",
        precomp_to_affine=True,
        use_init=False,
        use_multiply=True,
    )
    # Only the final result should be converted to affine, because we ignore precomp.
    assert set(affine_multiples) == {full_ctx.points[out]}
    # Only the single add in the multiply should be checked.
    assert set(add_multiples) == {(16, -1)}

    # Doing use_init = False and use_multiply = False does not make sense.
    with pytest.raises(ValueError):
        errors_out(
            precomp_ctx,
            full_ctx,
            out,
            check_funcs={"affine": affine_check, "add": add_check},
            check_condition="all",
            precomp_to_affine=True,
            use_init=False,
            use_multiply=False,
        )


@pytest.fixture(
    params=[
        (
            SlidingWindowMultiplier,
            dict(width=2, recoding_direction=ProcessingDirection.LTR),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=3, recoding_direction=ProcessingDirection.LTR),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=4, recoding_direction=ProcessingDirection.LTR),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=5, recoding_direction=ProcessingDirection.LTR),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=6, recoding_direction=ProcessingDirection.LTR),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=2, recoding_direction=ProcessingDirection.RTL),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=3, recoding_direction=ProcessingDirection.RTL),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=4, recoding_direction=ProcessingDirection.RTL),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=5, recoding_direction=ProcessingDirection.RTL),
        ),
        (
            SlidingWindowMultiplier,
            dict(width=6, recoding_direction=ProcessingDirection.RTL),
        ),
        (FixedWindowLTRMultiplier, dict(m=2**1)),
        (FixedWindowLTRMultiplier, dict(m=2**2)),
        (FixedWindowLTRMultiplier, dict(m=2**3)),
        (FixedWindowLTRMultiplier, dict(m=2**4)),
        (FixedWindowLTRMultiplier, dict(m=2**5)),
        (FixedWindowLTRMultiplier, dict(m=2**6)),
        (WindowBoothMultiplier, dict(width=2)),
        (WindowBoothMultiplier, dict(width=3)),
        (WindowBoothMultiplier, dict(width=4)),
        (WindowBoothMultiplier, dict(width=5)),
        (WindowBoothMultiplier, dict(width=6)),
        (WindowNAFMultiplier, dict(width=2)),
        (WindowNAFMultiplier, dict(width=3)),
        (WindowNAFMultiplier, dict(width=4)),
        (WindowNAFMultiplier, dict(width=5)),
        (WindowNAFMultiplier, dict(width=6)),
        (BinaryNAFMultiplier, dict(always=False, direction=ProcessingDirection.LTR)),
        (BinaryNAFMultiplier, dict(always=False, direction=ProcessingDirection.RTL)),
        (BinaryNAFMultiplier, dict(always=True, direction=ProcessingDirection.LTR)),
        (BinaryNAFMultiplier, dict(always=True, direction=ProcessingDirection.RTL)),
        (CombMultiplier, dict(width=2, always=True)),
        (CombMultiplier, dict(width=3, always=True)),
        (CombMultiplier, dict(width=4, always=True)),
        (CombMultiplier, dict(width=5, always=True)),
        (CombMultiplier, dict(width=6, always=True)),
        (CombMultiplier, dict(width=2, always=False)),
        (CombMultiplier, dict(width=3, always=False)),
        (CombMultiplier, dict(width=4, always=False)),
        (CombMultiplier, dict(width=5, always=False)),
        (CombMultiplier, dict(width=6, always=False)),
        (BGMWMultiplier, dict(width=2, direction=ProcessingDirection.LTR)),
        (BGMWMultiplier, dict(width=3, direction=ProcessingDirection.LTR)),
        (BGMWMultiplier, dict(width=4, direction=ProcessingDirection.LTR)),
        (BGMWMultiplier, dict(width=5, direction=ProcessingDirection.LTR)),
        (BGMWMultiplier, dict(width=6, direction=ProcessingDirection.LTR)),
        (BGMWMultiplier, dict(width=2, direction=ProcessingDirection.RTL)),
        (BGMWMultiplier, dict(width=3, direction=ProcessingDirection.RTL)),
        (BGMWMultiplier, dict(width=4, direction=ProcessingDirection.RTL)),
        (BGMWMultiplier, dict(width=5, direction=ProcessingDirection.RTL)),
        (BGMWMultiplier, dict(width=6, direction=ProcessingDirection.RTL)),
        (LTRMultiplier, dict(always=False, complete=True)),
        (LTRMultiplier, dict(always=True, complete=True)),
        (LTRMultiplier, dict(always=False, complete=False)),
        (LTRMultiplier, dict(always=True, complete=False)),
        (RTLMultiplier, dict(always=False, complete=True)),
        (RTLMultiplier, dict(always=True, complete=True)),
        (RTLMultiplier, dict(always=False, complete=False)),
        (RTLMultiplier, dict(always=True, complete=False)),
        (CoronMultiplier, dict()),
        (FullPrecompMultiplier, dict(always=False, complete=True)),
        (FullPrecompMultiplier, dict(always=True, complete=True)),
        (FullPrecompMultiplier, dict(always=False, complete=False)),
        (FullPrecompMultiplier, dict(always=True, complete=False)),
        (SimpleLadderMultiplier, dict(complete=True)),
        (SimpleLadderMultiplier, dict(complete=False)),
    ],
    ids=lambda p: f"{p[0].__name__}-{','.join(f'{k}={v}' for k, v in p[1].items())}",
)
def mult(secp128r1, request):
    mult_class, mult_kwargs = request.param
    return mult_class, partial(mult_class, **mult_kwargs)


@pytest.fixture()
def toy_params():
    model = ShortWeierstrassModel()
    coords = model.coordinates["projective"]
    p = 0xCB5E1D94A6168511
    a = mod(0xB166CA7D2DFBF69F, p)
    b = mod(0x855BB40CB6937C4B, p)
    gx = mod(0x253B2638BD13D6F4, p)
    gy = mod(0x1E91A1A182287E71, p)

    infty = InfinityPoint(coords)
    g = Point(coords, X=gx, Y=gy, Z=mod(1, p))
    curve = EllipticCurve(model, coords, p, infty, dict(a=a, b=b))
    return DomainParameters(curve, g, 0xCB5E1D94601A3AC5, 1)


def test_plot(toy_params, mult, plot_path):
    mult_class, mult_factory = mult
    precomp_ctx, full_ctx, out = multiple_graph(
        scalar=15546875464546546545644687 % toy_params.order,
        params=toy_params,
        mult_class=mult_class,
        mult_factory=mult_factory,
    )
    fig = graph_plot(precomp_ctx, full_ctx, out)
    fig.savefig(str(plot_path()) + ".png")


def test_independent_check_inputs(secp128r1, mult):
    """
    Check that the set of check inputs is constant if (use_init = True, use_multiply = False) for all scalars
    so that it only depends on the multiplier, countermeasure and error model, not particular scalars.
    """
    mult_class, mult_factory = mult
    for check_condition in ("all", "necessary"):
        for precomp_to_affine in (True, False):
            last_check_inputs = None
            for i in range(20):
                scalar = random.getrandbits(secp128r1.order.bit_length())
                precomp_ctx, full_ctx, out = multiple_graph(
                    scalar=scalar,
                    params=secp128r1,
                    mult_class=mult_class,
                    mult_factory=mult_factory,
                )
                check_inputs = graph_to_check_inputs(
                    precomp_ctx,
                    full_ctx,
                    out,
                    check_condition=check_condition,
                    precomp_to_affine=precomp_to_affine,
                    use_init=True,
                    use_multiply=False,
                )
                if last_check_inputs is not None:
                    assert (
                        check_inputs == last_check_inputs
                    ), f"Failed for {check_condition}, precomp_to_affine={precomp_to_affine}, scalar={scalar}, mult={mult_class.__name__}"
                else:
                    last_check_inputs = check_inputs


@pytest.mark.parametrize(
    "check_condition,precomp_to_affine,multiples_kind",
    [
        ("all", True, "all"),
        ("all", False, "all"),
        ("necessary", True, "precomp+necessary"),
        ("necessary", False, "necessary"),
    ],
)
def test_consistency_multiples(
    secp128r1,
    mult,
    check_condition,
    precomp_to_affine,
    multiples_kind,
):
    """
    Test consistency between the graph_to_check_inputs and multiples_computed functions for the same error model
    """
    for _ in range(10):
        mult_class, mult_factory = mult
        scalar = random.getrandbits(secp128r1.order.bit_length())
        precomp_ctx, full_ctx, out = multiple_graph(
            scalar=scalar,
            params=secp128r1,
            mult_class=mult_class,
            mult_factory=mult_factory,
        )
        check_inputs = graph_to_check_inputs(
            precomp_ctx,
            full_ctx,
            out,
            check_condition=check_condition,
            precomp_to_affine=precomp_to_affine,
        )
        # Now map the check inputs to the set of multiples they cover
        multiples_from_check_inputs = set()
        for (k,) in check_inputs.get("neg", []):
            multiples_from_check_inputs.add(k)
            multiples_from_check_inputs.add(-k)
        for (k,) in check_inputs.get("affine", []):
            multiples_from_check_inputs.add(k)
        for k, l in check_inputs.get("add", []):
            multiples_from_check_inputs.add(k)
            multiples_from_check_inputs.add(l)
            multiples_from_check_inputs.add(k + l)
        for (k,) in check_inputs.get("dbl", []):
            multiples_from_check_inputs.add(k)
            multiples_from_check_inputs.add(2 * k)
        # Multiples computed removes the zero
        multiples_from_check_inputs.discard(0)

        # Now compute the multiples via the other function to compare.
        multiples = multiples_from_graph(
            precomp_ctx, full_ctx, out, kind=multiples_kind
        )
        assert multiples_from_check_inputs == multiples
