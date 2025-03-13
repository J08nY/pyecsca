"""
Provides functions for computing division polynomials and the multiplication-by-n map on an elliptic curve.
"""

from typing import Tuple, Dict, Set, Mapping, Optional
from public import public
import warnings

from sympy import symbols, FF, Poly
import networkx as nx

from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.model import ShortWeierstrassModel

has_pari = False
try:
    import cypari2

    has_pari = True
except ImportError:
    cypari2 = None


def values(*ns: int) -> Mapping[int, Tuple[int, ...]]:
    done: Set[int] = set()
    vals = {}
    todo: Set[int] = set()
    todo.update(ns)
    while todo:
        val = todo.pop()
        if val in done:
            continue
        new: Tuple[int, ...] = ()
        if val == -2:
            new = (-1,)
        elif val == -1:
            pass
        elif val < 0:
            raise ValueError(f"bad {val}")
        elif val in (0, 1, 2, 3):
            pass
        elif val == 4:
            new = (-2, 3)
        elif val % 2 == 0:
            m = (val - 2) // 2
            new = (m + 1, m + 3, m, m - 1, m + 2)
        else:
            m = (val - 1) // 2
            if m % 2 == 0:
                new = (-2, m + 2, m, m - 1, m + 1)
            else:
                new = (m + 2, m, -2, m - 1, m + 1)
        if new:
            todo.update(new)
        vals[val] = new
        done.add(val)
    return vals


def dep_graph(*ns: int):
    g = nx.DiGraph()
    vals = values(*ns)
    for k, v in vals.items():
        if v:
            for e in v:
                g.add_edge(k, e)
        else:
            g.add_node(k)
    return g, vals


def dep_map(*ns: int):
    g, vals = dep_graph(*ns)
    current: Set[int] = set()
    ls = []
    for vert in nx.lexicographical_topological_sort(g, key=lambda v: -sum(g[v].keys())):
        if vert in current:
            current.remove(vert)
        ls.append((vert, set(current)))
        current.update(vals[vert])
    ls.reverse()
    return ls, vals


@public
def a_invariants(curve: EllipticCurve) -> Tuple[Mod, ...]:
    """
    Compute the a-invariants of the curve.

    :param curve: The elliptic curve (only ShortWeierstrass model).
    :return: A tuple of 5 a-invariants (a1, a2, a3, a4, a6).
    """
    if isinstance(curve.model, ShortWeierstrassModel):
        a1 = mod(0, curve.prime)
        a2 = mod(0, curve.prime)
        a3 = mod(0, curve.prime)
        a4 = curve.parameters["a"]
        a6 = curve.parameters["b"]
        return a1, a2, a3, a4, a6
    else:
        raise NotImplementedError


@public
def b_invariants(curve: EllipticCurve) -> Tuple[Mod, ...]:
    """
    Compute the b-invariants of the curve.

    :param curve: The elliptic curve (only ShortWeierstrass model).
    :return: A tuple of 4 b-invariants (b2, b4, b6, b8).
    """
    if isinstance(curve.model, ShortWeierstrassModel):
        a1, a2, a3, a4, a6 = a_invariants(curve)
        return (
            a1 * a1 + 4 * a2,
            a1 * a3 + 2 * a4,
            a3**2 + 4 * a6,
            a1**2 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3**2 - a4**2,
        )
    else:
        raise NotImplementedError


def divpoly0(curve: EllipticCurve, *ns: int) -> Mapping[int, Poly]:
    """
    Basically sagemath's division_polynomial_0 but more clever memory management.

    As sagemath says:

        Return the `n^{th}` torsion (division) polynomial, without
        the 2-torsion factor if `n` is even, as a polynomial in `x`.

        These are the polynomials `g_n` defined in [MT1991]_, but with
        the sign flipped for even `n`, so that the leading coefficient is
        always positive.

    :param curve: The elliptic curve.
    :param ns: The values to compute the polynomial for.
    :return:
    """
    xs = symbols("x")

    K = FF(curve.prime)
    Kx = lambda r: Poly(r, xs, domain=K)  # noqa

    x = Kx(xs)

    b2, b4, b6, b8 = map(lambda b: Kx(int(b)), b_invariants(curve))
    ls, _ = dep_map(*ns)

    mem: Dict[int, Poly] = {}
    for i, keep in ls:
        if i == -2:
            val = mem[-1] ** 2
        elif i == -1:
            val = Kx(4) * x**3 + b2 * x**2 + Kx(2) * b4 * x + b6
        elif i == 0:
            val = Kx(0)
        elif i < 0:
            raise ValueError("n must be a positive integer (or -1 or -2)")
        elif i in (1, 2):
            val = Kx(1)
        elif i == 3:
            val = Kx(3) * x**4 + b2 * x**3 + Kx(3) * b4 * x**2 + Kx(3) * b6 * x + b8
        elif i == 4:
            val = -mem[-2] + (Kx(6) * x**2 + b2 * x + b4) * mem[3]
        elif i % 2 == 0:
            m = (i - 2) // 2
            val = mem[m + 1] * (mem[m + 3] * mem[m] ** 2 - mem[m - 1] * mem[m + 2] ** 2)
        else:
            m = (i - 1) // 2
            if m % 2 == 0:
                val = mem[-2] * mem[m + 2] * mem[m] ** 3 - mem[m - 1] * mem[m + 1] ** 3
            else:
                val = mem[m + 2] * mem[m] ** 3 - mem[-2] * mem[m - 1] * mem[m + 1] ** 3
        for dl in set(mem.keys()).difference(keep).difference(ns):
            del mem[dl]
        mem[i] = val

    return mem


@public
def divpoly(curve: EllipticCurve, n: int, two_torsion_multiplicity: int = 2) -> Poly:
    """
    Compute the n-th division polynomial.

    :param curve: Curve to compute on.
    :param n: Scalar.
    :param two_torsion_multiplicity: Same as sagemath.
    :return: The division polynomial.
    """
    f: Poly = divpoly0(curve, n)[n]
    a1, a2, a3, a4, a6 = a_invariants(curve)
    xs, ys = symbols("x y")
    x = Poly(xs, xs, domain=f.domain)
    y = Poly(ys, ys, domain=f.domain)

    if two_torsion_multiplicity == 0:
        return f
    elif two_torsion_multiplicity == 1:
        if n % 2 == 0:
            Kxy = lambda r: Poly(r, xs, ys, domain=f.domain)  # noqa
            return Kxy(f) * (Kxy(2) * y + Kxy(a1) * x + Kxy(a3))
        else:
            return f
    elif two_torsion_multiplicity == 2:
        if n % 2 == 0:
            return f * divpoly0(curve, -1)[-1]
        else:
            return f
    else:
        raise ValueError


def mult_by_n_own(curve: EllipticCurve, n: int) -> Tuple[Poly, Poly]:
    xs, ys = symbols("x y")
    K = FF(curve.prime)
    x = Poly(xs, xs, domain=K)
    Kxy = lambda r: Poly(r, xs, ys, domain=K)  # noqa

    if n == 1:
        return x, Kxy(1)

    polys = divpoly0(curve, -2, -1, n - 1, n, n + 1, n + 2)
    # TODO: All of these fractions may benefit from using
    #       sympy.cancel to get rid of common factors in the numerator and denominator.
    #       Though for large polynomials that might be too much.
    mx_denom = polys[n] ** 2
    if n % 2 == 0:
        mx_num = x * polys[-1] * polys[n] ** 2 - polys[n - 1] * polys[n + 1]
        mx_denom *= polys[-1]
    else:
        mx_num = x * polys[n] ** 2 - polys[-1] * polys[n - 1] * polys[n + 1]

    # Alternative that makes the denominator monic by dividing the
    # numerator by the leading coefficient. Sage does this
    # simplification when asking for multiplication_by_m with the
    # x-only=True, as then the poly is an univariate object.
    # >
    # > lc = K(mx_denom.LC())
    # > mx = (mx_num.quo(lc), mx_denom.monic())
    mx = (mx_num, mx_denom)
    return mx


if has_pari:

    def mult_by_n_pari(curve: EllipticCurve, n: int):
        pari = cypari2.Pari()
        # Magic heuristic, plus some constant term for very small polys
        stacksize = 2 * (n**2 * (40 * curve.prime.bit_length())) + 1000000
        stacksizemax = 15 * stacksize

        pari.default("debugmem", 0)  # silence stack warnings
        pari.allocatemem(stacksize, stacksizemax, silent=True)
        p = pari(curve.prime)
        a = pari.Mod(curve.parameters["a"], p)
        b = pari.Mod(curve.parameters["b"], p)
        E = pari.ellinit([a, b])
        while True:
            try:
                mx = pari.ellxn(E, n)
                break
            except cypari2.PariError as e:
                if e.errnum() == 17:  # out of stack memory
                    pari.allocatemem(0)
                else:
                    raise e
        x = symbols("x")
        K = FF(curve.prime)
        mx_num = Poly([int(coeff) for coeff in reversed(mx[0])], x, domain=K)
        mx_denom = Poly([int(coeff) for coeff in reversed(mx[1])], x, domain=K)
        return mx_num, mx_denom


@public
def mult_by_n(
    curve: EllipticCurve, n: int, x_only: bool = False, use_pari: bool = True
) -> Tuple[Tuple[Poly, Poly], Optional[Tuple[Poly, Poly]]]:
    """
    Compute the multiplication-by-n map on an elliptic curve.

    :param curve: Curve to compute on.
    :param n: Scalar.
    :param x_only: Whether to skip the my computation.
    :param use_pari: Whether to use the Pari version.
    :return: A tuple (mx, my) where each is a tuple (numerator, denominator).
    """
    if use_pari and has_pari:
        mx = mult_by_n_pari(curve, n)
    else:
        if use_pari:
            warnings.warn(
                "Falling-back to slow mult-by-n map computation due to missing [pari] (cypari2 and libpari) dependency."
            )
        mx = mult_by_n_own(curve, n)

    if x_only:
        return mx, None

    xs, ys = symbols("x y")
    K = FF(curve.prime)
    x = Poly(xs, xs, domain=K)
    y = Poly(ys, ys, domain=K)
    Kxy = lambda r: Poly(r, xs, ys, domain=K)  # noqa

    a1, a2, a3, a4, a6 = a_invariants(curve)

    # The following lines compute
    # my = ((2*y+a1*x+a3)*mx.derivative(x)/m - a1*mx-a3)/2
    # just as sage does, but using sympy and step-by-step
    # tracking the numerator and denominator of the fraction.

    # > mx.derivative()
    mxd_num = mx[1] * mx[0].diff() - mx[0] * mx[1].diff()
    mxd_denom = mx[1] ** 2

    # > mx.derivative()/m
    mxd_dn_num = mxd_num
    mxd_dn_denom = mxd_denom * Kxy(n)

    # > (2*y+a1*x+a3)*mx.derivative(x)/m
    mxd_full_num = mxd_dn_num * (Kxy(2) * y + Kxy(a1) * x + Kxy(a3))
    mxd_full_denom = mxd_dn_denom

    # > a1*mx
    a1mx_num = Kxy(a1) * mx[0]
    a1mx_denom = mx[1]  # noqa

    # > a3
    a3_num = Kxy(a3) * mx[1]
    a3_denom = mx[1]  # noqa

    # The mx.derivative part has a different denominator, basically mx[1]^2 * m
    # so the rest needs to be multiplied by this factor when subtracting.
    mxd_fact = mx[1] * n

    my_num = mxd_full_num - a1mx_num * mxd_fact - a3_num * mxd_fact
    my_denom = mxd_full_denom * Kxy(2)
    my = (my_num, my_denom)
    return mx, my
