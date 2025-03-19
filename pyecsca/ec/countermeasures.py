"""Provides several countermeasures against side-channel attacks."""

from abc import ABC, abstractmethod
from typing import Optional

from public import public

from pyecsca.ec.formula import AdditionFormula
from pyecsca.ec.mod import Mod, mod
from pyecsca.ec.mult import ScalarMultiplier, ScalarMultiplicationAction
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


@public
class ScalarMultiplierCountermeasure(ABC):
    """
    A scalar multiplier-based countermeasure.

    This class behaves like a scalar multiplier, in fact it wraps one
    and provides some scalar-splitting countermeasure.
    """

    mult: ScalarMultiplier
    params: Optional[DomainParameters]
    point: Optional[Point]

    def __init__(self, mult: ScalarMultiplier):
        self.mult = mult

    def init(self, params: DomainParameters, point: Point):
        """Initialize the countermeasure with the parameters and the point."""
        self.params = params
        self.point = point
        self.mult.init(self.params, self.point)

    @abstractmethod
    def multiply(self, scalar: int) -> Point:
        """
        Multiply the point with the scalar using the countermeasure.

        .. note::
            The countermeasure may compute multiple scalar multiplications internally.
            Thus, it may call the init method of the scalar multiplier multiple times.

        :param scalar: The scalar to multiply with.
        :return: The result of the multiplication.
        """
        raise NotImplementedError


@public
class GroupScalarRandomization(ScalarMultiplierCountermeasure):
    r"""
    Group scalar randomization countermeasure.

    Samples a random multiple, multiplies the order with it and adds it to the scalar.

    .. math::
        :class: frame

        &r \xleftarrow{\$} \{0, 1, \ldots, 2^{\text{rand_bits}}\} \\
        &\textbf{return}\ [k + r n]G

    """

    rand_bits: int

    def __init__(self, mult: ScalarMultiplier, rand_bits: int = 32):
        """
        :param mult: The multiplier to use.
        :param rand_bits: How many random bits to sample.
        """
        super().__init__(mult)
        self.rand_bits = rand_bits

    def init(self, params: DomainParameters, point: Point):
        self.params = params
        self.point = point
        self.mult.init(
            self.params,
            self.point,
            bits=params.full_order.bit_length() + self.rand_bits,
        )

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            order = self.params.order
            mask = int(Mod.random(1 << self.rand_bits))
            masked_scalar = scalar + mask * order
            return action.exit(self.mult.multiply(masked_scalar))


@public
class AdditiveSplitting(ScalarMultiplierCountermeasure):
    r"""
    Additive splitting countermeasure.

    Splits the scalar into two parts additively, multiplies the point with them and adds the results.

    .. math::
        :class: frame

        &r \xleftarrow{\$} \{0, 1, \ldots, n\} \\
        &\textbf{return}\ [k - r]G + [r]G

    """

    add: Optional[AdditionFormula]

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None):
        """
        :param mult: The multiplier to use.
        :param add: Addition formula to use, if None, the formula from the multiplier is used.
        """
        super().__init__(mult)
        self.add = add

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            order = self.params.order
            r = Mod.random(order)
            s = scalar - r
            R = self.mult.multiply(int(r))
            S = self.mult.multiply(int(s))
            if self.add is None:
                res = self.mult._add(R, S)  # noqa: This is OK.
            else:
                res = self.add(
                    self.params.curve.prime, R, S, **self.params.curve.parameters
                )[0]
            return action.exit(res)


@public
class MultiplicativeSplitting(ScalarMultiplierCountermeasure):
    r"""
    Multiplicative splitting countermeasure.

    Splits the scalar into two parts multiplicatively, multiplies the point with them and adds the results.

    .. math::
        :class: frame

        &r \xleftarrow{\$} \{0, 1, \ldots, 2^{\text{rand_bits}}\} \\
        &S = [r]G \\
        &\textbf{return}\ [k r^{-1} \mod n]S

    """

    rand_bits: int

    def __init__(self, mult: ScalarMultiplier, rand_bits: int = 32):
        """
        :param mult: The multiplier to use.
        :param rand_bits: How many random bits to sample.
        """
        super().__init__(mult)
        self.rand_bits = rand_bits

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            r = Mod.random(1 << self.rand_bits)
            R = self.mult.multiply(int(r))

            self.mult.init(self.params, R)
            kr_inv = scalar * mod(int(r), self.params.order).inverse()
            return action.exit(self.mult.multiply(int(kr_inv)))


@public
class EuclideanSplitting(ScalarMultiplierCountermeasure):
    r"""
    Euclidean splitting countermeasure.

    Picks a random value half the size of the curve, then splits the scalar
    into the remainder and the quotient of the division by the random value.

    .. math::
        :class: frame

        &r \xleftarrow{\$} \{0, 1, \ldots, 2^{\log_2{(n)}/2}\} \\
        &S = [r]G \\
        &k_1 = k \mod r \\
        &k_2 = \lfloor \frac{k}{r} \rfloor \\
        &\textbf{return}\ [k_1]G + [k_2]S

    """

    add: Optional[AdditionFormula]

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None):
        """
        :param mult: The multiplier to use.
        :param add: Addition formula to use, if None, the formula from the multiplier is used.
        """
        super().__init__(mult)
        self.add = add

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            half_bits = self.params.order.bit_length() // 2
            r = Mod.random(1 << half_bits)
            R = self.mult.multiply(int(r))

            k1 = scalar % int(r)
            k2 = scalar // int(r)
            T = self.mult.multiply(k1)

            self.mult.init(self.params, R)
            S = self.mult.multiply(k2)

            if self.add is None:
                res = self.mult._add(S, T)  # noqa: This is OK.
            else:
                res = self.add(
                    self.params.curve.prime, S, T, **self.params.curve.parameters
                )[0]
            return action.exit(res)


@public
class BrumleyTuveri(ScalarMultiplierCountermeasure):
    r"""
    A countermeasure that fixes the bit-length of the scalar by adding some multiple
    of the order to it.

    Originally proposed in [BT11]_.

    .. math::
        :class: frame

        &\hat{k}= \begin{cases}
            k + 2n \quad \text{if } \lceil \log_2(k+n) \rceil = \lceil \log_2 n \rceil\\
            k + n \quad \text{otherwise}.
        \end{cases}\\
        &\textbf{return}\ [\hat{k}]G

    """

    def init(self, params: DomainParameters, point: Point):
        self.params = params
        self.point = point
        self.mult.init(
            self.params,
            self.point,
            bits=params.full_order.bit_length() + 1,
        )

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            n = self.params.full_order
            scalar += n
            if scalar.bit_length() <= n.bit_length():
                scalar += n
            return action.exit(self.mult.multiply(scalar))
