"""Provides (mostly abstract) base classes for multi-scalar multipliers and the actions used in them."""

from abc import ABC, abstractmethod
from typing import List, Optional

from public import public

from pyecsca.ec.context import ResultAction
from pyecsca.ec.mult.base import MultiplierBase
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


@public
class MultiScalarMultiplierAction(ResultAction):
    """A multi-scalar multiplication of points on a curve by scalars."""

    points: List[Point]
    params: DomainParameters
    scalars: List[int]

    def __init__(self, points: List[Point], params: DomainParameters, scalars: List[int]):
        super().__init__()
        self.points = points
        self.params = params
        self.scalars = scalars

    def __repr__(self):
        return f"{self.__class__.__name__}({self.points}, {self.params}, {self.scalars})"


@public
class MultiScalarMultiplier(MultiplierBase, ABC):
    """
    A multi-scalar multiplication algorithm.

    A multi-scalar multiplier computes the linear combination of a fixed set of points with a
    set of scalars, i.e. the sum of the products of each point with its scalar.

    .. note::
        The __init__ method of all concrete subclasses needs to have type annotations so that
        configuration enumeration works.

    :param short_circuit: Whether the use of formulas will be guarded by short-circuit on inputs
                          of the point at infinity.
    :param formulas: Formulas this instance will use.
    """

    _params: DomainParameters
    _bits: int

    def __hash__(self):
        return hash(
            (
                MultiScalarMultiplier,
                tuple(self.formulas.keys()),
                tuple(self.formulas.values()),
                self.short_circuit,
            )
        )

    def __eq__(self, other):
        if not isinstance(other, MultiScalarMultiplier):
            return False
        return (
            self.formulas == other.formulas
            and self.short_circuit == other.short_circuit
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(str, self.formulas.values()))}, short_circuit={self.short_circuit})"

    def init(
        self, params: DomainParameters, points: List[Point], bits: Optional[int] = None
    ):
        """
        Initialize the multi-scalar multiplier with :paramref:`~.init.params` and a list of
        :paramref:`~.init.points`.

        .. warning::
            The points are not verified to be on the curve represented in the domain parameters.

        :param params: The domain parameters to initialize the multiplier with.
        :param points: The points to initialize the multiplier with.
        :param bits: The number of bits to use in the multi-scalar multiplication (i.e. no scalar
                     will be larger than 2^bits). The default is the bit length of the full order
                     of the curve (including cofactor).
        """
        coord_model = set(self.formulas.values()).pop().coordinate_model
        if params.curve.coordinate_model != coord_model:
            raise ValueError(
                "Coordinate models of the parameters and formulas are not compatible."
            )
        for point in points:
            if point.coordinate_model != coord_model:
                raise ValueError(
                    "Coordinate models of the parameters, formulas or a point are not compatible."
                )
        self._params = params
        self._bits = bits if bits is not None else params.full_order.bit_length()
        self._initialized = True

    @abstractmethod
    def multiply(self, scalars: List[int]) -> Point:
        """
        Compute the multi-scalar product of the points the multiplier was initialized with.

        .. note::
            The multiplier needs to be initialized by a call to the :py:meth:`.init` method.

        :param scalars: The scalars to use, one per point the multiplier was initialized with.
        :return: The resulting linear combination.
        """
        raise NotImplementedError
