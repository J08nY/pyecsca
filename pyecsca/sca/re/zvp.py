"""
Provides functionality inspired by the Zero-value point attack.

  Zero-Value Point Attacks on Elliptic Curve Cryptosystem, Toru Akishita & Tsuyoshi Takagi , ISC '03
  `<https://doi.org/10.1007/10958513_17>`_
"""
from typing import Tuple, Dict, Union, Set

from sympy import symbols, FF, Poly
import networkx as nx

from pyecsca.ec.context import DefaultContext, local
from pyecsca.ec.curve import EllipticCurve
from pyecsca.ec.formula import Formula
from pyecsca.ec.mod import SymbolicMod, Mod
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.point import Point
from pyecsca.misc.cfg import TemporaryConfig


def unroll_formula(formula: Formula, prime: int):
    inputs = [Point(formula.coordinate_model,
                    **{var: SymbolicMod(symbols(var + str(i)), prime) for var in formula.coordinate_model.variables})
              for i in
              range(1, 1 + formula.num_inputs)]
    params = {var: SymbolicMod(symbols(var), prime) for var in formula.coordinate_model.curve_model.parameter_names}
    with local(DefaultContext()) as ctx, TemporaryConfig() as cfg:
        cfg.ec.mod_implementation = "symbolic"
        formula(prime, *inputs, **params)
    return [op_result.value for op_result in ctx.actions.get_by_index([0])[0].op_results]


def values(*ns: int):
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
        elif val <= 0:
            raise ValueError(f"bad {val}")
        elif val == 1 or val == 2 or val == 3:
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


def a_invariants(curve: EllipticCurve) -> Tuple[Mod, ...]:
    if isinstance(curve.model, ShortWeierstrassModel):
        a1 = Mod(0, curve.prime)
        a2 = Mod(0, curve.prime)
        a3 = Mod(0, curve.prime)
        a4 = curve.parameters["a"]
        a6 = curve.parameters["b"]
        return a1, a2, a3, a4, a6
    else:
        raise NotImplementedError


def b_invariants(curve: EllipticCurve) -> Tuple[Mod, ...]:
    if isinstance(curve.model, ShortWeierstrassModel):
        a1, a2, a3, a4, a6 = a_invariants(curve)
        return (a1 * a1 + 4 * a2,
                a1 * a3 + 2 * a4,
                a3 ** 2 + 4 * a6,
                a1 ** 2 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 ** 2 - a4 ** 2)
    else:
        raise NotImplementedError


def divpoly0(curve: EllipticCurve, *ns: int) -> Union[Poly, Tuple[Poly, ...]]:
    # Basically sagemath's division_polynomial_0 but more clever memory management
    # and dependency computation.
    xs = symbols("x")

    K = FF(curve.prime)
    Kx = lambda r: Poly(r, xs, domain=K)

    x = Kx(xs)

    b2, b4, b6, b8 = map(lambda b: Kx(int(b)), b_invariants(curve))
    ls, vals = dep_map(*ns)

    mem: Dict[int, Poly] = {}
    for i, keep in ls:
        if i == -2:
            val = mem[-1] ** 2
        elif i == -1:
            val = Kx(4) * x ** 3 + b2 * x ** 2 + Kx(2) * b4 * x + b6
        elif i <= 0:
            raise ValueError("n must be a positive integer (or -1 or -2)")
        elif i == 1 or i == 2:
            val = Kx(1)
        elif i == 3:
            val = Kx(3) * x ** 4 + b2 * x ** 3 + Kx(3) * b4 * x ** 2 + Kx(3) * b6 * x + b8
        elif i == 4:
            val = -mem[-2] + (Kx(6) * x ** 2 + b2 * x + b4) * mem[3]
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

    if len(ns) == 1:
        return mem[ns[0]]
    else:
        return tuple(mem[n] for n in ns)


def divpoly(curve: EllipticCurve, n: int, two_torsion_multiplicity: int = 2) -> Poly:
    f: Poly = divpoly0(curve, n)
    a1, a2, a3, a4, a6 = a_invariants(curve)
    xs, ys = symbols("x y")
    x = Poly(xs, xs, domain=f.domain)
    y = Poly(ys, ys, domain=f.domain)

    if two_torsion_multiplicity == 0:
        return f
    elif two_torsion_multiplicity == 1:
        if n % 2 == 0:
            Kxy = lambda r: Poly(r, xs, ys, domain=f.domain)
            return Kxy(f) * (Kxy(2) * y + Kxy(a1) * x + Kxy(a3))
        else:
            return f
    elif two_torsion_multiplicity == 2:
        if n % 2 == 0:
            return f * divpoly0(curve, -1)
        else:
            return f


def mult_by_n(curve: EllipticCurve, n: int) -> Tuple[Poly, Poly]:
    xs = symbols("x")
    K = FF(curve.prime)
    x = Poly(xs, xs, domain=K)

    if n == 1:
        return x

    polys = divpoly0(curve, -2, -1, n - 1, n, n + 1)
    denom = polys[3] ** 2
    if n % 2 == 0:
        num = x * polys[1] * polys[3] ** 2 - polys[2] * polys[4]
        denom *= polys[1]
    else:
        num = x * polys[3] ** 2 - polys[1] * polys[2] * polys[4]
    lc = K(denom.LC())
    return num.quo(lc), denom.monic()
