"""Provides (mostly abstract) base classes for scalar multipliers, enums used to specify their parameters
and actions used in them."""

from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from public import public
from typing import Mapping, Tuple, Optional, ClassVar, Set, Type

from pyecsca.ec.context import ResultAction
from pyecsca.ec.formula import Formula
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


@public
class ProcessingDirection(Enum):
    """Scalar processing direction."""

    LTR = "Left-to-right"
    RTL = "Right-to-left"


@public
class AccumulationOrder(Enum):
    """Accumulation order (makes a difference for the projective result)."""

    PeqPR = "P = P + R"
    PeqRP = "P = R + P"


@public
class ScalarMultiplicationAction(ResultAction):
    """A scalar multiplication of a point on a curve by a scalar."""

    point: Point
    params: DomainParameters
    scalar: int

    def __init__(self, point: Point, params: DomainParameters, scalar: int):
        super().__init__()
        self.point = point
        self.params = params
        self.scalar = scalar

    def __repr__(self):
        return f"{self.__class__.__name__}({self.point}, {self.params}, {self.scalar})"


@public
class PrecomputationAction(ResultAction):
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

    .. note::
        The __init__ method of all concrete subclasses needs to have type annotations so that
        configuration enumeration works.

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param formulas: Formulas this instance will use.
    """

    requires: ClassVar[Set[Type]]  # Type[Formula] but mypy has a false positive
    """The set of formula types that the multiplier requires."""
    optionals: ClassVar[Set[Type]]  # Type[Formula] but mypy has a false positive
    """The optional set of formula types that the multiplier can use."""
    short_circuit: bool
    """Whether the formulas will short-circuit upon input of the point at infinity."""
    formulas: Mapping[str, Formula]
    """All formulas the multiplier was initialized with."""
    _params: DomainParameters
    _point: Point
    _bits: int
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
            raise ValueError("Formulas need to belong to the same coordinate model.")
        self.short_circuit = short_circuit
        self.formulas = {k: v for k, v in formulas.items() if v is not None}
        found_required = set()
        for formula in self.formulas.values():
            for required in self.requires:
                if isinstance(formula, required):
                    found_required.add(required)
                    break
            else:
                for optional in self.optionals:
                    if isinstance(formula, optional):
                        break
                else:
                    raise ValueError("Not required or optional formulas provided.")
        if found_required != self.requires:
            raise ValueError("Required formulas missing.")

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
        if self.short_circuit and point == self._params.curve.neutral:
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
        return hash(
            (
                ScalarMultiplier,
                tuple(self.formulas.keys()),
                tuple(self.formulas.values()),
                self.short_circuit,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, ScalarMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit})"

    def init(self, params: DomainParameters, point: Point, bits: Optional[int] = None):
        """
        Initialize the scalar multiplier with :paramref:`~.init.params` and a :paramref:`~.init.point`.

        .. warning::
            The point is not verified to be on the curve represented in the domain parameters.

        :param params: The domain parameters to initialize the multiplier with.
        :param point: The point to initialize the multiplier with.
        :param bits: The number of bits to use in the scalar multiplication (i.e. no scalar will be larger than 2^bits).
                     The default is the bit length of the full order of the curve (including cofactor).
        """
        coord_model = set(self.formulas.values()).pop().coordinate_model
        if (
            params.curve.coordinate_model != coord_model
            or point.coordinate_model != coord_model
        ):
            raise ValueError(
                "Coordinate models of the parameters, formulas or point are not compatible."
            )
        self._params = params
        self._point = point
        self._bits = bits if bits is not None else params.full_order.bit_length()
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
class PrecompMultiplier(ScalarMultiplier, ABC):
    pass


@public
class AccumulatorMultiplier(ScalarMultiplier, ABC):
    """
    A scalar multiplication algorithm mix-in class for a multiplier that accumulates.

    :param accumulation_order: The order of accumulation of points.
    """

    accumulation_order: AccumulationOrder
    """The order of accumulation of points."""

    def __init__(
        self,
        *args,
        accumulation_order: AccumulationOrder = AccumulationOrder.PeqPR,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.accumulation_order = accumulation_order

    def _accumulate(self, p: Point, r: Point) -> Point:
        if self.accumulation_order is AccumulationOrder.PeqPR:
            p = self._add(p, r)
        elif self.accumulation_order is AccumulationOrder.PeqRP:
            p = self._add(r, p)
        return p
