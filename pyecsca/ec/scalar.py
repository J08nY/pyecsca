"""Provides functions for computing various scalar representations (like NAF, or different bases)."""
from typing import List

from public import public


@public
def convert(i: int, base: int) -> List[int]:
    """
    Convert an integer to base.

    :param i:
    :param base:
    :return:
    """
    if i == 0:
        return [0]
    res = []
    while i:
        i, r = divmod(i, base)
        res.append(r)
    return res


@public
def wnaf(k: int, w: int) -> List[int]:
    """
    Compute width `w` NAF (Non-Adjacent Form) of the scalar `k`.

    :param k: The scalar.
    :param w: The width.
    :return: The NAF.
    """
    half_width = 2 ** (w - 1)
    full_width = half_width * 2

    def mods(val: int) -> int:
        val_mod = val % full_width
        if val_mod > half_width:
            val_mod -= full_width
        return val_mod

    result: List[int] = []
    while k >= 1:
        if k & 1:
            k_val = mods(k)
            result.insert(0, k_val)
            k -= k_val
        else:
            result.insert(0, 0)
        k >>= 1
    return result


@public
def naf(k: int) -> List[int]:
    """
    Compute the NAF (Non-Adjacent Form) of the scalar `k`.

    :param k: The scalar.
    :return: The NAF.
    """
    return wnaf(k, 2)
