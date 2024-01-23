"""Cache some things."""
from functools import lru_cache
from sympy import sympify as _orig_sympify, simplify as _orig_simplify, count_ops
from public import public


@public
@lru_cache(maxsize=256, typed=True)
def sympify(
    a, locals=None, convert_xor=True, strict=False, rational=False, evaluate=None
):
    return _orig_sympify(a, locals, convert_xor, strict, rational, evaluate)


@public
@lru_cache(maxsize=256, typed=True)
def simplify(expr, ratio=1.7, measure=count_ops, rational=False, inverse=False, doit=True, **kwargs):
    return _orig_simplify(expr, ratio=ratio, measure=measure, rational=rational, inverse=inverse, doit=doit, **kwargs)
