"""
Provides functionality inspired by the Refined-Power Analysis attack by Goubin [RPA]_.
"""

from copy import copy, deepcopy
from functools import lru_cache

from public import public
from typing import (
    MutableMapping,
    Optional,
    Callable,
    List,
    Set,
    cast,
    Type,
    Literal,
    Union,
)

from sympy import FF, sympify, Poly, symbols

from pyecsca.ec.error import NonInvertibleError
from pyecsca.ec.formula.fake import FakePoint
from pyecsca.sca.re.base import RE
from pyecsca.sca.re.tree import Tree, Map
from pyecsca.ec.coordinates import AffineCoordinateModel
from pyecsca.ec.formula import (
    FormulaAction,
    DoublingFormula,
    AdditionFormula,
    TriplingFormula,
    NegationFormula,
    DifferentialAdditionFormula,
    LadderFormula, ScalingFormula,
)
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.mult import (
    ScalarMultiplicationAction,
    PrecomputationAction,
    ScalarMultiplier,
)
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.model import ShortWeierstrassModel, MontgomeryModel
from pyecsca.ec.point import Point
from pyecsca.ec.context import Context, Action, local
from pyecsca.ec.mult.fake import fake_mult
from pyecsca.misc.utils import log, warn


@public
class MultipleContext(Context):
    """Context that traces the multiples of points computed."""

    base: Optional[Point]
    """The base point that all the multiples are counted from."""
    neutral: Optional[Point]
    """The neutral point used in the computation."""
    points: MutableMapping[Point, int]
    """The mapping of points to the multiples they represent (e.g., base -> 1)."""
    parents: MutableMapping[Point, List[Point]]
    """The mapping of points to their parent they were computed from."""
    formulas: MutableMapping[Point, str]
    """The mapping of points to the formula types they are a result of."""
    precomp: MutableMapping[int, Point]
    """The mapping of precomputed multiples to the points they represent."""
    inside: List[Action]
    """Whether we are inside a scalarmult/precomp action."""
    keep_base: bool
    """Whether to keep the base point when building upon it."""

    def __init__(self, keep_base: bool = False):
        self.base = None
        self.points = {}
        self.parents = {}
        self.formulas = {}
        self.precomp = {}
        self.inside = []
        self.keep_base = keep_base

    def enter_action(self, action: Action) -> None:
        if isinstance(action, (ScalarMultiplicationAction, PrecomputationAction)):
            self.inside.append(action)
            if self.base:
                # If we already did some computation with this context try to see if we are building on top of it.
                if self.base != action.point:
                    # We are not doing the same point, but maybe we are doing a multiple of it.
                    if action.point in self.points and self.keep_base:
                        # We are doing a multiple of the base and were asked to keep it.
                        pass
                    else:
                        # We are not building on top of it (or were asked to forget).
                        # We have to forget stuff and set a new base and mapping.
                        self.base = action.point
                        self.neutral = action.params.curve.neutral
                        self.points = {self.base: 1, self.neutral: 0}
                        self.parents = {self.base: [], self.neutral: []}
                        self.formulas = {self.base: "", self.neutral: ""}
                        self.precomp = {}
            else:
                self.base = action.point
                self.neutral = action.params.curve.neutral
                self.points = {self.base: 1, self.neutral: 0}
                self.parents = {self.base: [], self.neutral: []}
                self.formulas = {self.base: "", self.neutral: ""}
                self.precomp = {}

    def exit_action(self, action: Action) -> None:
        if isinstance(action, (ScalarMultiplicationAction, PrecomputationAction)):
            self.inside.remove(action)
            if isinstance(action, PrecomputationAction):
                self.precomp.update(action.result)
        if isinstance(action, FormulaAction) and self.inside:
            action = cast(FormulaAction, action)
            shortname = action.formula.shortname
            if shortname == "dbl":
                inp = action.input_points[0]
                out = action.output_points[0]
                self.points[out] = 2 * self.points[inp]
                self.parents[out] = [inp]
                self.formulas[out] = action.formula.shortname
            elif shortname == "tpl":
                inp = action.input_points[0]
                out = action.output_points[0]
                self.points[out] = 3 * self.points[inp]
                self.parents[out] = [inp]
                self.formulas[out] = action.formula.shortname
            elif shortname == "add":
                one, other = action.input_points
                out = action.output_points[0]
                self.points[out] = self.points[one] + self.points[other]
                self.parents[out] = [one, other]
                self.formulas[out] = action.formula.shortname
            elif shortname == "neg":
                inp = action.input_points[0]
                out = action.output_points[0]
                self.points[out] = -self.points[inp]
                self.parents[out] = [inp]
                self.formulas[out] = action.formula.shortname
            elif shortname == "dadd":
                _, one, other = action.input_points
                out = action.output_points[0]
                self.points[out] = self.points[one] + self.points[other]
                self.parents[out] = [one, other]
                self.formulas[out] = action.formula.shortname
            elif shortname == "ladd":
                _, one, other = action.input_points
                dbl, add = action.output_points
                self.points[add] = self.points[one] + self.points[other]
                self.parents[add] = [one, other]
                self.formulas[add] = action.formula.shortname
                self.points[dbl] = 2 * self.points[one]
                self.parents[dbl] = [one]
                self.formulas[dbl] = action.formula.shortname
            elif shortname == "scl":
                inp = action.input_points[0]
                out = action.output_points[0]
                self.points[out] = self.points[inp]
                self.parents[out] = [inp]
                self.formulas[out] = action.formula.shortname

    def __repr__(self):
        return f"{self.__class__.__name__}({self.base!r}, multiples={self.points.values()!r})"


@public
def rpa_point_0y(params: DomainParameters) -> Optional[Point]:
    """Construct an (affine) [RPA]_ point (0, y) for given domain parameters."""
    if isinstance(params.curve.model, ShortWeierstrassModel):
        if not params.curve.parameters["b"].is_residue():
            return None
        y = params.curve.parameters["b"].sqrt()
        # TODO: We can take the negative as well.
        return Point(
            AffineCoordinateModel(params.curve.model), x=mod(0, params.curve.prime), y=y
        )
    elif isinstance(params.curve.model, MontgomeryModel):
        return Point(
            AffineCoordinateModel(params.curve.model),
            x=mod(0, params.curve.prime),
            y=mod(0, params.curve.prime),
        )
    else:
        raise NotImplementedError


@public
def rpa_point_x0(params: DomainParameters) -> Optional[Point]:
    """Construct an (affine) [RPA]_ point (x, 0) for given domain parameters."""
    if isinstance(params.curve.model, ShortWeierstrassModel):
        if (params.order * params.cofactor) % 2 != 0:
            return None
        k = FF(params.curve.prime)
        expr = sympify("x^3 + a * x + b", evaluate=False)
        expr = expr.subs("a", k(int(params.curve.parameters["a"])))
        expr = expr.subs("b", k(int(params.curve.parameters["b"])))
        poly = Poly(expr, symbols("x"), domain=k)
        roots = poly.ground_roots()
        if not roots:
            return None
        x = mod(int(next(iter(roots.keys()))), params.curve.prime)
        return Point(
            AffineCoordinateModel(params.curve.model), x=x, y=mod(0, params.curve.prime)
        )
    elif isinstance(params.curve.model, MontgomeryModel):
        return Point(
            AffineCoordinateModel(params.curve.model),
            x=mod(0, params.curve.prime),
            y=mod(0, params.curve.prime),
        )
    else:
        raise NotImplementedError


@public
def rpa_input_point(k: Mod, rpa_point: Point, params: DomainParameters) -> Point:
    """Construct an (affine) input point P that will lead to an RPA point [k]P."""
    kinv = k.inverse()
    return params.curve.affine_multiply(rpa_point, int(kinv))


@public
def rpa_distinguish(
    params: DomainParameters,
    multipliers: List[ScalarMultiplier],
    oracle: Callable[[int, Point], bool],
    bound: Optional[int] = None,
    tries: int = 10,
    majority: int = 1,
    use_init: bool = True,
    use_multiply: bool = True,
) -> Set[ScalarMultiplier]:
    """
    Distinguish the scalar multiplier used (from the possible :paramref:`~.rpa_distinguish.multipliers`) using
    an [RPA]_ :paramref:`~.rpa_distinguish.oracle`.

    :param params: The domain parameters to use.
    :param multipliers: The list of possible multipliers.
    :param oracle: An oracle that returns `True` when an RPA point is encountered during scalar multiplication of the input by the scalar.
    :param bound: A bound on the size of the scalar to consider.
    :param tries: Number of tries to get a non-trivial tree.
    :param majority: Query the oracle up to `majority` times and take the majority vote of the results.
    :param use_init: Whether to consider the point multiples that happen in scalarmult initialization.
    :param use_multiply: Whether to consider the point multiples that happen in scalarmult multiply (after initialization).
    :return: The list of possible multipliers after distinguishing (ideally just one).
    """
    re = RPA(set(multipliers))
    re.build_tree(params, tries, bound, use_init, use_multiply)
    return re.run(oracle, majority)


@public
class RPA(RE):
    """RPA-based RE."""

    params: Optional[DomainParameters] = None
    """The domain parameters to use."""
    P0: Optional[Point] = None
    """The zero-coordinate point that will be used in the RE."""
    scalars: Optional[List[int]] = None
    """A list of scalars that will be used in the RE."""

    def build_tree(
        self,
        params: DomainParameters,
        tries: int = 10,
        bound: Optional[int] = None,
        use_init: bool = True,
        use_multiply: bool = True,
    ):
        """
        Build an RPA distinguishing tree.

        :param params: The domain parameters to use.
        :param tries: Number of tries to get a non-trivial tree.
        :param bound: A bound on the size of the scalar to consider.
        :param use_init: Whether to consider the point multiples that happen in scalarmult initialization.
        :param use_multiply: Whether to consider the point multiples that happen in scalarmult multiply (after initialization).
        """
        if not (use_init or use_multiply):
            raise ValueError("Has to use either init or multiply or both.")
        P0 = rpa_point_0y(params)
        if not P0:
            raise ValueError("There are no RPA-points on the provided curve.")
        if not bound:
            bound = params.order

        mults = {copy(mult) for mult in self.configs}
        init_contexts = {}
        for mult in mults:
            with local(MultipleContext()) as ctx:
                mult.init(params, params.generator)
            init_contexts[mult] = ctx

        done = 0
        tree = None
        scalars = []
        while True:
            scalar = int(Mod.random(bound))
            log(f"Got scalar {scalar}")
            log([mult.__class__.__name__ for mult in mults])
            mults_to_multiples = {}
            for mult in mults:
                # Copy the context after init to not accumulate multiples by accident here.
                init_context = deepcopy(init_contexts[mult])
                # Take the computed points during init
                init_points = set(init_context.parents.keys())
                # And get their parents (inputs to formulas)
                init_parents = set(
                    sum((init_context.parents[point] for point in init_points), [])
                )
                # Go over the parents and map them to multiples of the base (plus-minus sign)
                init_multiples = set(
                    map(
                        lambda v: mod(v, params.order),
                        (init_context.points[parent] for parent in init_parents),
                    )
                )
                init_multiples |= set(map(lambda v: -v, init_multiples))
                # Now do the multiply and repeat the above, but only consider new computed points
                with local(init_context) as ctx:
                    mult.multiply(scalar)
                all_points = set(ctx.parents.keys())
                multiply_parents = set(
                    sum((ctx.parents[point] for point in all_points - init_points), [])
                )
                multiply_multiples = set(
                    map(
                        lambda v: mod(v, params.order),
                        (ctx.points[parent] for parent in multiply_parents),
                    )
                )
                multiply_multiples |= set(map(lambda v: -v, multiply_multiples))
                # Use only the multiples from the correct part (init vs multiply)
                used = set()
                if use_init:
                    used |= init_multiples
                if use_multiply:
                    used |= multiply_multiples
                # Filter out the multiples that are non-invertible because they are not usable for RPA.
                usable = set()
                for elem in used:
                    try:
                        elem.inverse()
                        usable.add(elem)
                    except NonInvertibleError:
                        pass
                mults_to_multiples[mult] = usable

            dmap = Map.from_sets(set(mults), mults_to_multiples)
            if tree is None:
                tree = Tree.build(set(mults), dmap)
            else:
                tree = tree.expand(dmap)

            log("Built distinguishing tree.")
            log(tree.render())
            scalars.append(scalar)
            if not tree.precise:
                done += 1
                if done > tries:
                    warn(
                        f"Tried more than {tries} times. Aborting. Distinguishing may not be precise."
                    )
                    break
                else:
                    continue
            else:
                break
        self.scalars = scalars
        self.tree = tree
        self.params = params
        self.P0 = P0

    def run(
        self, oracle: Callable[[int, Point], bool], majority: int = 1
    ) -> Set[ScalarMultiplier]:
        """
        Run the RPA-RE with an `oracle`.

        :param oracle: An oracle that returns `True` when an RPA point is encountered during scalar multiplication of the input by the scalar.
        :param majority: Query the oracle up to `majority` times and take the majority vote of the results.
        :return: The set of possible multipliers.
        """
        if (
            self.tree is None
            or self.scalars is None
            or self.P0 is None
            or self.params is None
        ):
            raise ValueError("Need to build tree first.")

        if (majority % 2) == 0:
            raise ValueError("Cannot use even majority.")

        current_node = self.tree.root
        mults = current_node.cfgs
        while current_node.children:
            scalar = self.scalars[current_node.dmap_index]  # type: ignore
            best_distinguishing_multiple: Mod = current_node.dmap_input  # type: ignore
            P0_inverse = rpa_input_point(
                best_distinguishing_multiple, self.P0, self.params
            )
            responses = []
            response = True
            for _ in range(majority):
                responses.append(oracle(scalar, P0_inverse))
                if responses.count(True) > (majority // 2):
                    response = True
                    break
                if responses.count(False) > (majority // 2):
                    response = False
                    break
            log(f"Oracle response -> {response}")
            response_map = {child.response: child for child in current_node.children}
            current_node = response_map[response]
            mults = current_node.cfgs
            log([mult.__class__.__name__ for mult in mults])
            log()
        return mults


@lru_cache(maxsize=256, typed=True)
def _cached_fake_mult(
    mult_class: Type[ScalarMultiplier], mult_factory: Callable, params: DomainParameters
) -> ScalarMultiplier:
    fm = fake_mult(mult_class, mult_factory, params)
    if getattr(fm, "short_circuit", False):
        raise ValueError("The multiplier must not short-circuit.")
    return fm


@public
def multiples_computed(
    scalar: int,
    params: DomainParameters,
    mult_class: Type[ScalarMultiplier],
    mult_factory: Callable,
    use_init: bool = True,
    use_multiply: bool = True,
    kind: Union[
        Literal["all"],
        Literal["input"],
        Literal["necessary"],
        Literal["precomp+necessary"],
    ] = "all",
) -> set[int]:
    """
    Compute the multiples computed for a given scalar and multiplier (quickly).

    :param scalar: The scalar to compute for.
    :param params: The domain parameters to use.
    :param mult_class: The class of the scalar multiplier to use.
    :param mult_factory: A callable that takes the formulas and instantiates the multiplier.
    :param use_init: Whether to consider the point multiples that happen in scalarmult initialization.
    :param use_multiply: Whether to consider the point multiples that happen in scalarmult multiply (after initialization).
    :param kind: The kind of multiples to return. Can be one of "all", "input", "necessary", or "precomp+necessary".
    :return: A list of tuples, where the first element is the formula shortname (e.g. "add") and the second is a tuple of the dlog
    relationships to the input of the input points to the formula.

    .. note::
        The scalar multiplier must not short-circuit.
        If `kind` is not "all", `use_init` must be `True`.
    """
    if kind != "all" and not use_init:
        raise ValueError("Cannot use kind other than 'all' with use_init=False.")

    mult = _cached_fake_mult(mult_class, mult_factory, params)
    ctx = MultipleContext(keep_base=True)
    if use_init:
        with local(ctx, copy=False):
            mult.init(params, FakePoint(params.curve.coordinate_model))
    else:
        mult.init(params, FakePoint(params.curve.coordinate_model))

    if use_multiply:
        with local(ctx, copy=False):
            out = mult.multiply(scalar)
    else:
        out = mult.multiply(scalar)

    if kind == "all":
        res = set(ctx.points.values())
    elif kind == "input":
        res = set()
        for point, multiple in ctx.points.items():
            if point in ctx.parents:
                for parent in ctx.parents[point]:
                    res.add(ctx.points[parent])
    elif kind == "necessary":
        res = {ctx.points[out]}
        queue = {out}
        while queue:
            point = queue.pop()
            for parent in ctx.parents[point]:
                res.add(ctx.points[parent])
                queue.add(parent)
    elif kind == "precomp+necessary":
        res = {ctx.points[out]}
        queue = {out, *ctx.precomp.values()}
        while queue:
            point = queue.pop()
            for parent in ctx.parents[point]:
                res.add(ctx.points[parent])
                queue.add(parent)
    else:
        raise ValueError(f"Invalid kind {kind}")
    return res - {0}
