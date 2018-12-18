from public import public
from typing import List


@public
def wnaf(k: int, w: int) -> List[int]:
    """
    Compute width `w` NAF (Non-Adjacent Form) of the scalar `k`.

    :param k:
    :param w:
    :return:
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

    :param k:
    :return:
    """
    return wnaf(k, 2)
