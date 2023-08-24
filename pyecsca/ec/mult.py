"""Provides several classes implementing different scalar multiplication algorithms."""
from abc import ABC, abstractmethod
from copy import copy
from typing import Mapping, Tuple, Optional, MutableMapping, ClassVar, Set, Type
from math import log2

from public import public

from .context import ResultAction, Action
from .formula import (
    Formula,
    AdditionFormula,
    DoublingFormula,
    DifferentialAdditionFormula,
    ScalingFormula,
    LadderFormula,
    NegationFormula,
)
from .scalar import wnaf, naf, convert
from .params import DomainParameters
from .point import Point


@public
class ScalarMultiplicationAction(ResultAction):
    """A scalar multiplication of a point on a curve by a scalar."""

    point: Point
    scalar: int

    def __init__(self, point: Point, scalar: int):
        super().__init__()
        self.point = point
        self.scalar = scalar

    def __repr__(self):
        return f"{self.__class__.__name__}({self.point}, {self.scalar})"


@public
class PrecomputationAction(Action):
    """A precomputation of a point in scalar multiplication."""

    params: DomainParameters
    point: Point

    def __init__(self, params: DomainParameters, point: Point):
        super().__init__()
        self.params = params
        self.point = point

    def __repr__(self):
        return f"{self.__class__.__name__}({self.params}, {self.point})"


@public
class ScalarMultiplier(ABC):
    """
    A scalar multiplication algorithm.

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param formulas: Formulas this instance will use.
    """

    requires: ClassVar[Set[Type]]  # Type[Formula] but mypy has a false positive
    """The set of formulas that the multiplier requires."""
    optionals: ClassVar[Set[Type]]  # Type[Formula] but mypy has a false positive
    """The optional set of formulas that the multiplier can use."""
    short_circuit: bool
    """Whether the formulas will short-circuit upon input of the point at infinity."""
    formulas: Mapping[str, Formula]
    """All formulas the multiplier was initialized with."""
    _params: DomainParameters
    _point: Point
    _initialized: bool = False

    def __init__(self, short_circuit: bool = True, **formulas: Optional[Formula]):
        if (
                len(
                    {
                        formula.coordinate_model
                        for formula in formulas.values()
                        if formula is not None
                    }
                )
                != 1
        ):
            raise ValueError
        self.short_circuit = short_circuit
        self.formulas = {k: v for k, v in formulas.items() if v is not None}

    def _add(self, one: Point, other: Point) -> Point:
        if "add" not in self.formulas:
            raise NotImplementedError
        if self.short_circuit:
            if one == self._params.curve.neutral:
                return copy(other)
            if other == self._params.curve.neutral:
                return copy(one)
        return self.formulas["add"](
            self._params.curve.prime, one, other, **self._params.curve.parameters
        )[0]

    def _dbl(self, point: Point) -> Point:
        if "dbl" not in self.formulas:
            raise NotImplementedError
        if (
                self.short_circuit
                and point == self._params.curve.neutral
        ):
            return copy(point)
        return self.formulas["dbl"](
            self._params.curve.prime, point, **self._params.curve.parameters
        )[0]

    def _scl(self, point: Point) -> Point:
        if "scl" not in self.formulas:
            raise NotImplementedError
        return self.formulas["scl"](
            self._params.curve.prime, point, **self._params.curve.parameters
        )[0]

    def _ladd(self, start: Point, to_dbl: Point, to_add: Point) -> Tuple[Point, ...]:
        if "ladd" not in self.formulas:
            raise NotImplementedError
        if self.short_circuit:
            if to_dbl == self._params.curve.neutral:
                return to_dbl, to_add
            if to_add == self._params.curve.neutral:
                return self._dbl(to_dbl), to_dbl
        return self.formulas["ladd"](
            self._params.curve.prime,
            start,
            to_dbl,
            to_add,
            **self._params.curve.parameters,
        )

    def _dadd(self, start: Point, one: Point, other: Point) -> Point:
        if "dadd" not in self.formulas:
            raise NotImplementedError
        if self.short_circuit:
            if one == self._params.curve.neutral:
                return copy(other)
            if other == self._params.curve.neutral:
                return copy(one)
        return self.formulas["dadd"](
            self._params.curve.prime, start, one, other, **self._params.curve.parameters
        )[0]

    def _neg(self, point: Point) -> Point:
        if "neg" not in self.formulas:
            raise NotImplementedError
        return self.formulas["neg"](
            self._params.curve.prime, point, **self._params.curve.parameters
        )[0]

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, ScalarMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit

    def __repr__(self):
        return f"{self.__class__.__name__}({tuple(self.formulas.values())}, short_circuit={self.short_circuit})"

    def init(self, params: DomainParameters, point: Point):
        """
        Initialize the scalar multiplier with :paramref:`~.init.params` and a :paramref:`~.init.point`.

        .. warning::
            The point is not verified to be on the curve represented in the domain parameters.

        :param params: The domain parameters to initialize the multiplier with.
        :param point: The point to initialize the multiplier with.
        """
        coord_model = set(self.formulas.values()).pop().coordinate_model
        if (
                params.curve.coordinate_model != coord_model
                or point.coordinate_model != coord_model
        ):
            raise ValueError
        self._params = params
        self._point = point
        self._initialized = True

    @abstractmethod
    def multiply(self, scalar: int) -> Point:
        """
        Multiply the point with the scalar.

        .. note::
            The multiplier needs to be initialized by a call to the :py:meth:`.init` method.

        :param scalar: The scalar to use.
        :return: The resulting multiple.
        """
        raise NotImplementedError


@public
class LTRMultiplier(ScalarMultiplier):
    """
    Classic double and add scalar multiplication algorithm, that scans the scalar left-to-right (msb to lsb).

    :param always: Whether the double and add always method is used.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    always: bool
    complete: bool

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            scl: Optional[ScalingFormula] = None,
            always: bool = False,
            complete: bool = True,
            short_circuit: bool = True,
    ):
        super().__init__(short_circuit=short_circuit, add=add, dbl=dbl, scl=scl)
        self.always = always
        self.complete = complete

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, LTRMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.always == other.always and self.complete == other.complete

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            if self.complete:
                q = self._point
                r = copy(self._params.curve.neutral)
                top = self._params.order.bit_length() - 1
            else:
                q = copy(self._point)
                r = copy(self._point)
                top = scalar.bit_length() - 2
            for i in range(top, -1, -1):
                r = self._dbl(r)
                if scalar & (1 << i) != 0:
                    # TODO: This order makes a difference in projective coordinates
                    r = self._add(r, q)
                elif self.always:
                    self._add(r, q)
            if "scl" in self.formulas:
                r = self._scl(r)
            return action.exit(r)


@public
class RTLMultiplier(ScalarMultiplier):
    """
    Classic double and add scalar multiplication algorithm, that scans the scalar right-to-left (lsb to msb).

    :param always: Whether the double and add always method is used.
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    always: bool

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            scl: Optional[ScalingFormula] = None,
            always: bool = False,
            short_circuit: bool = True,
    ):
        super().__init__(short_circuit=short_circuit, add=add, dbl=dbl, scl=scl)
        self.always = always

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, RTLMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.always == other.always

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            q = self._point
            r = copy(self._params.curve.neutral)
            while scalar > 0:
                if scalar & 1 != 0:
                    # TODO: This order makes a difference in projective coordinates
                    r = self._add(r, q)
                elif self.always:
                    self._add(r, q)
                q = self._dbl(q)
                scalar >>= 1
            if "scl" in self.formulas:
                r = self._scl(r)
            return action.exit(r)


@public
class CoronMultiplier(ScalarMultiplier):
    """
    Coron's double and add resistant against SPA.

    From:
    **Resistance against Differential Power Analysis for Elliptic Curve Cryptosystems**

    https://link.springer.com/content/pdf/10.1007/3-540-48059-5_25.pdf
    """

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            scl: Optional[ScalingFormula] = None,
            short_circuit: bool = True,
    ):
        super().__init__(short_circuit=short_circuit, add=add, dbl=dbl, scl=scl)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, CoronMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            q = self._point
            p0 = copy(q)
            for i in range(scalar.bit_length() - 2, -1, -1):
                p0 = self._dbl(p0)
                p1 = self._add(p0, q)
                if scalar & (1 << i) != 0:
                    p0 = p1
            if "scl" in self.formulas:
                p0 = self._scl(p0)
            return action.exit(p0)


@public
class LadderMultiplier(ScalarMultiplier):
    """Montgomery ladder multiplier, using a three input, two output ladder formula."""

    requires = {LadderFormula}
    optionals = {DoublingFormula, ScalingFormula}
    complete: bool

    def __init__(
            self,
            ladd: LadderFormula,
            dbl: Optional[DoublingFormula] = None,
            scl: Optional[ScalingFormula] = None,
            complete: bool = True,
            short_circuit: bool = True,
    ):
        super().__init__(short_circuit=short_circuit, ladd=ladd, dbl=dbl, scl=scl)
        self.complete = complete
        if (not complete or short_circuit) and dbl is None:
            raise ValueError

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, LadderMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.complete == other.complete

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            q = self._point
            if self.complete:
                p0 = copy(self._params.curve.neutral)
                p1 = self._point
                top = self._params.order.bit_length() - 1
            else:
                p0 = copy(q)
                p1 = self._dbl(q)
                top = scalar.bit_length() - 2
            for i in range(top, -1, -1):
                if scalar & (1 << i) == 0:
                    p0, p1 = self._ladd(q, p0, p1)
                else:
                    p1, p0 = self._ladd(q, p1, p0)
            if "scl" in self.formulas:
                p0 = self._scl(p0)
            return action.exit(p0)


@public
class SimpleLadderMultiplier(ScalarMultiplier):
    """Montgomery ladder multiplier, using addition and doubling formulas."""

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    complete: bool

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            scl: Optional[ScalingFormula] = None,
            complete: bool = True,
            short_circuit: bool = True,
    ):
        super().__init__(short_circuit=short_circuit, add=add, dbl=dbl, scl=scl)
        self.complete = complete

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, SimpleLadderMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.complete == other.complete

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            if self.complete:
                top = self._params.order.bit_length() - 1
            else:
                top = scalar.bit_length() - 1
            p0 = copy(self._params.curve.neutral)
            p1 = copy(self._point)
            for i in range(top, -1, -1):
                if scalar & (1 << i) == 0:
                    p1 = self._add(p0, p1)
                    p0 = self._dbl(p0)
                else:
                    p0 = self._add(p0, p1)
                    p1 = self._dbl(p1)
            if "scl" in self.formulas:
                p0 = self._scl(p0)
            return action.exit(p0)


@public
class DifferentialLadderMultiplier(ScalarMultiplier):
    """Montgomery ladder multiplier, using differential addition and doubling formulas."""

    requires = {DifferentialAdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    complete: bool

    def __init__(
            self,
            dadd: DifferentialAdditionFormula,
            dbl: DoublingFormula,
            scl: Optional[ScalingFormula] = None,
            complete: bool = True,
            short_circuit: bool = True,
    ):
        super().__init__(short_circuit=short_circuit, dadd=dadd, dbl=dbl, scl=scl)
        self.complete = complete

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, DifferentialLadderMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.complete == other.complete

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            if self.complete:
                top = self._params.order.bit_length() - 1
            else:
                top = scalar.bit_length() - 1
            q = self._point
            p0 = copy(self._params.curve.neutral)
            p1 = copy(q)
            for i in range(top, -1, -1):
                if scalar & (1 << i) == 0:
                    p1 = self._dadd(q, p0, p1)
                    p0 = self._dbl(p0)
                else:
                    p0 = self._dadd(q, p0, p1)
                    p1 = self._dbl(p1)
            if "scl" in self.formulas:
                p0 = self._scl(p0)
            return action.exit(p0)


@public
class BinaryNAFMultiplier(ScalarMultiplier):
    """Binary NAF (Non Adjacent Form) multiplier, left-to-right."""

    requires = {AdditionFormula, DoublingFormula, NegationFormula}
    optionals = {ScalingFormula}
    _point_neg: Point

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            neg: NegationFormula,
            scl: Optional[ScalingFormula] = None,
            short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit, add=add, dbl=dbl, neg=neg, scl=scl
        )

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, BinaryNAFMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            self._point_neg = self._neg(point)

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            scalar_naf = naf(scalar)
            q = copy(self._params.curve.neutral)
            for val in scalar_naf:
                q = self._dbl(q)
                if val == 1:
                    q = self._add(q, self._point)
                if val == -1:
                    q = self._add(q, self._point_neg)
            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)


@public
class WindowNAFMultiplier(ScalarMultiplier):
    """Window NAF (Non Adjacent Form) multiplier, left-to-right."""

    requires = {AdditionFormula, DoublingFormula, NegationFormula}
    optionals = {ScalingFormula}
    _points: MutableMapping[int, Point]
    _points_neg: MutableMapping[int, Point]
    precompute_negation: bool = False
    width: int

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            neg: NegationFormula,
            width: int,
            scl: Optional[ScalingFormula] = None,
            precompute_negation: bool = False,
            short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit, add=add, dbl=dbl, neg=neg, scl=scl
        )
        self.width = width
        self.precompute_negation = precompute_negation

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, WindowNAFMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.width == other.width and self.precompute_negation == other.precompute_negation

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            self._points = {}
            self._points_neg = {}
            current_point = point
            double_point = self._dbl(point)
            for i in range(0, 2 ** (self.width - 2)):
                self._points[2 * i + 1] = current_point
                if self.precompute_negation:
                    self._points_neg[2 * i + 1] = self._neg(current_point)
                current_point = self._add(current_point, double_point)

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            scalar_naf = wnaf(scalar, self.width)
            q = copy(self._params.curve.neutral)
            for val in scalar_naf:
                q = self._dbl(q)
                if val > 0:
                    q = self._add(q, self._points[val])
                elif val < 0:
                    if self.precompute_negation:
                        neg = self._points_neg[-val]
                    else:
                        neg = self._neg(self._points[-val])
                    q = self._add(q, neg)
            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)


@public
class FixedWindowLTRMultiplier(ScalarMultiplier):
    """Like LTRMultiplier, but not binary, but m-ary."""

    requires = {AdditionFormula, DoublingFormula}
    optionals = {ScalingFormula}
    complete: bool
    m: int
    _points: MutableMapping[int, Point]

    def __init__(
            self,
            add: AdditionFormula,
            dbl: DoublingFormula,
            m: int,
            scl: Optional[ScalingFormula] = None,
            short_circuit: bool = True,
    ):
        super().__init__(
            short_circuit=short_circuit, add=add, dbl=dbl, scl=scl
        )
        if m < 2:
            raise ValueError("Invalid window width.")
        self.m = m

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if not isinstance(other, FixedWindowLTRMultiplier):
            return False
        return self.formulas == other.formulas and self.short_circuit == other.short_circuit and self.m == other.m

    def init(self, params: DomainParameters, point: Point):
        with PrecomputationAction(params, point):
            super().init(params, point)
            double_point = self._dbl(point)
            self._points = {1: point, 2: double_point}
            current_point = double_point
            for i in range(3, self.m):
                current_point = self._add(current_point, point)
                self._points[i] = current_point

    def _mult_m(self, point: Point) -> Point:
        if self.m & (self.m - 1) == 0:
            q = point
            for _ in range(int(log2(self.m))):
                q = self._dbl(q)
        else:
            r = copy(point)
            q = self._dbl(point)
            for _ in range(self.m - 2):
                q = self._add(q, r)
        return q

    def multiply(self, scalar: int) -> Point:
        if not self._initialized:
            raise ValueError("ScalarMultiplier not initialized.")
        with ScalarMultiplicationAction(self._point, scalar) as action:
            if scalar == 0:
                return action.exit(copy(self._params.curve.neutral))
            # General case (any m) and special case (m = 2^k) are handled together here
            converted = convert(scalar, self.m)
            q = copy(self._params.curve.neutral)
            for digit in reversed(converted):
                q = self._mult_m(q)
                if digit != 0:
                    q = self._add(q, self._points[digit])
            if "scl" in self.formulas:
                q = self._scl(q)
            return action.exit(q)
