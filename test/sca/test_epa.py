from functools import partial

from pyecsca.ec.mult import LTRMultiplier, CombMultiplier
from pyecsca.sca import multiple_graph
from pyecsca.sca.re.epa import errors_out


def test_errors_out(secp128r1):
    ctx, out = multiple_graph(
        scalar=15,
        params=secp128r1,
        mult_class=LTRMultiplier,
        mult_factory=LTRMultiplier,
    )
    res_empty_checks = errors_out(
        ctx,
        out,
        check_funcs={},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert not res_empty_checks

    def add_check(k, l):  # noqa
        return k == 6

    res_check_k_add = errors_out(
        ctx,
        out,
        check_funcs={"add": add_check},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert res_check_k_add

    def affine_check(k):
        return k == 15

    res_check_k_affine = errors_out(
        ctx,
        out,
        check_funcs={"affine": affine_check},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert res_check_k_affine


def test_errors_out_comb(secp128r1):
    ctx, out = multiple_graph(
        scalar=15,
        params=secp128r1,
        mult_class=CombMultiplier,
        mult_factory=partial(CombMultiplier, width=2),
    )

    def affine_check_comb(k):
        return k == 2**64

    res_check_k_affine_precomp = errors_out(
        ctx,
        out,
        check_funcs={"affine": affine_check_comb},
        check_condition="all",
        precomp_to_affine=True,
    )
    assert res_check_k_affine_precomp

    res_check_k_no_affine_precomp = errors_out(
        ctx,
        out,
        check_funcs={"affine": affine_check_comb},
        check_condition="all",
        precomp_to_affine=False,
    )
    assert not res_check_k_no_affine_precomp
