"""Provides functions for computing various scalar representations (like NAF, or different bases)."""
from typing import List
from itertools import dropwhile
from public import public


@public
def convert_base(i: int, base: int) -> List[int]:
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
def sliding_window_ltr(i: int, w: int) -> List[int]:
    """
    Compute the sliding-window left-to-right form.
    From https://eprint.iacr.org/2017/627.pdf.

    :param i:
    :param w:
    :return:
    """
    result: List[int] = []
    b = i.bit_length() - 1
    while b >= 0:
        val = i & (1 << b)
        if not val:
            result.append(0)
            b -= 1
        else:
            u = 0
            for v in range(1, w + 1):
                if b + 1 < v:
                    break
                mask = ((2**v) - 1) << (b - v + 1)
                c = (i & mask) >> (b - v + 1)
                if c & 1:
                    u = c
            k = u.bit_length()
            result.extend([0] * (k - 1))
            result.append(u)
            b -= k
    return list(dropwhile(lambda x: x == 0, result))


@public
def sliding_window_rtl(i: int, w: int) -> List[int]:
    """
    Compute the sliding-window right-to-left form.
    From https://eprint.iacr.org/2017/627.pdf.

    :param i: The scalar.
    :param w: The width.
    :return: The sliding-window RTL form.
    """
    result: List[int] = []
    while i >= 1:
        val = i & 1
        if not val:
            result = [0] + result
            i >>= 1
        else:
            window = i & ((2**w) - 1)
            result = ([0] * (w - 1)) + [window] + result
            i >>= w

    return list(dropwhile(lambda x: x == 0, result))


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
