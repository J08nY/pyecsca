"""Cache some things."""
from functools import lru_cache
from sympy import sympify as _orig_sympify
from public import public


@public
@lru_cache(maxsize=256, typed=True)
def sympify(
    a, locals=None, convert_xor=True, strict=False, rational=False, evaluate=None
):
    return _orig_sympify(a, locals, convert_xor, strict, rational, evaluate)
