from functools import partial

import pytest

from pyecsca.ec.coordinates import EFDCoordinateModel
from pyecsca.ec.mult import LTRMultiplier, CombMultiplier, WindowNAFMultiplier
from pyecsca.sca.re.rpa import multiple_graph
from pyecsca.sca.re.epa import errors_out


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
        mult_factory=partial(WindowNAFMultiplier, width=3, complete=False, precompute_negation=True),
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
    assert set(add_multiples) == {(1, 2), (3, 2)}

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
    assert set(affine_multiples) == set(precomp_ctx.precomp.keys()) | {full_ctx.points[out]}
    # The add multiples should be the same as before, plus any inputs to add that happened
    # during the final multiply, there is only one, rest are doubles.
    assert set(add_multiples) == {(1, 2), (3, 2), (16, -1)}

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
