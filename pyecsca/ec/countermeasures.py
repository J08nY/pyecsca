"""Provides several countermeasures against side-channel attacks."""

from abc import ABC, abstractmethod
from typing import Optional, Callable, get_type_hints, ClassVar, Set, Type

from public import public

from pyecsca.ec.formula import AdditionFormula, NegationFormula
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

    mults: list["ScalarMultiplier | ScalarMultiplierCountermeasure"]
    """The underlying scalar multipliers (or another countermeasure)."""
    nmults: ClassVar[int]
    """The number of scalar multipliers required."""
    requires: ClassVar[Set[Type]]  # Type[Formula] but mypy has a false positive
    """The formulas required by the countermeasure."""
    params: Optional[DomainParameters]
    """The domain parameters, if any."""
    point: Optional[Point]
    """The point to multiply, if any."""
    bits: Optional[int]
    """The bit-length to use, if any."""

    def __init__(
        self,
        *mults: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        rng: Callable[[int], Mod] = Mod.random,
    ):
        self.mults = list(mults)
        if len(self.mults) != self.nmults:
            raise ValueError(
                f"Expected {self.nmults} multipliers, got {len(self.mults)}."
            )
        self.rng = rng

    def init(self, params: DomainParameters, point: Point, bits: Optional[int] = None):
        """Initialize the countermeasure with the parameters and the point."""
        self.params = params
        self.point = point
        if bits is None:
            bits = params.full_order.bit_length()
        self.bits = bits

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

    @classmethod
    def from_single(
        cls, mult: "ScalarMultiplier | ScalarMultiplierCountermeasure", **kwargs
    ):
        """
        Create an instance of the countermeasure from a single scalar multiplier.

        :param mult: The scalar multiplier to use.
        :return: An instance of the countermeasure.
        """
        mults = [mult] * cls.nmults
        return cls(*mults, **kwargs)

    def _apply_formula(self, shortname: str, *points: Point) -> Point:
        if formula := getattr(self, shortname, None):
            if self.params is None:
                raise ValueError("Not initialized.")
            return formula(
                self.params.curve.prime,
                *points,
                **self.params.curve.parameters,  # type: ignore
            )[0]
        else:
            for mult in self.mults:
                if mult_formula := getattr(mult, f"_{shortname}", None):
                    try:
                        return mult_formula(*points)  # type: ignore
                    except ValueError:
                        pass
            else:
                raise ValueError(f"No formula '{shortname}' available.")

    def _add(self, R: Point, S: Point) -> Point:  # noqa
        return self._apply_formula("add", R, S)

    def _neg(self, P: Point) -> Point:
        return self._apply_formula("neg", P)


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

    nmults = 1
    requires = set()
    rand_bits: int

    def __init__(
        self,
        mult: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        rng: Callable[[int], Mod] = Mod.random,
        rand_bits: int = 32,
    ):
        """
        :param mult: The multiplier to use.
        :param rng: The random number generator to use.
        :param rand_bits: How many random bits to sample.
        """
        super().__init__(mult, rng=rng)
        self.rand_bits = rand_bits

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None or self.bits is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            order = self.params.order
            mask = int(self.rng(1 << self.rand_bits))
            masked_scalar = scalar + mask * order
            bits = max(self.bits, self.rand_bits + order.bit_length()) + 1
            self.mults[0].init(
                self.params,
                self.point,
                bits=bits,
            )
            return action.exit(self.mults[0].multiply(masked_scalar))


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

    nmults = 2
    requires = {AdditionFormula}
    add: Optional[AdditionFormula]

    def __init__(
        self,
        mult1: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        mult2: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        rng: Callable[[int], Mod] = Mod.random,
        add: Optional[AdditionFormula] = None,
    ):
        """
        :param mult1: The multiplier to use.
        :param mult2: The multiplier to use.
        :param rng: The random number generator to use.
        :param add: Addition formula to use, if None, the formula from the multiplier is used.
        """
        super().__init__(mult1, mult2, rng=rng)
        self.add = add

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None or self.bits is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            order = self.params.order
            r = self.rng(order)
            s = scalar - r
            bits = max(self.bits, order.bit_length())

            self.mults[0].init(self.params, self.point, bits)
            R = self.mults[0].multiply(int(r))

            self.mults[1].init(self.params, self.point, bits)
            S = self.mults[1].multiply(int(s))

            res = self._add(R, S)
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

    nmults = 2
    requires = set()
    rand_bits: int

    def __init__(
        self,
        mult1: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        mult2: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        rng: Callable[[int], Mod] = Mod.random,
        rand_bits: int = 32,
    ):
        """
        :param mult1: The multiplier to use.
        :param mult2: The multiplier to use.
        :param rng: The random number generator to use.
        :param rand_bits: How many random bits to sample.
        """
        super().__init__(mult1, mult2, rng=rng)
        self.rand_bits = rand_bits

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None or self.bits is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            r = self.rng(1 << self.rand_bits)
            self.mults[0].init(self.params, self.point, self.rand_bits)
            R = self.mults[0].multiply(int(r))

            self.mults[1].init(
                self.params, R, max(self.bits, self.params.order.bit_length())
            )
            kr_inv = scalar * mod(int(r), self.params.order).inverse()
            return action.exit(self.mults[1].multiply(int(kr_inv)))


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

    nmults = 3
    requires = {AdditionFormula}
    add: Optional[AdditionFormula]

    def __init__(
        self,
        mult1: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        mult2: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        mult3: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        rng: Callable[[int], Mod] = Mod.random,
        add: Optional[AdditionFormula] = None,
    ):
        """
        :param mult1: The multiplier to use.
        :param mult2: The multiplier to use.
        :param mult3: The multiplier to use.
        :param rng: The random number generator to use.
        :param add: Addition formula to use, if None, the formula from the multiplier is used.
        """
        super().__init__(mult1, mult2, mult3, rng=rng)
        self.add = add

    def _add(self, R: Point, S: Point) -> Point:  # noqa
        if self.add is None:
            for mult in self.mults:
                try:
                    return mult._add(R, S)  # type: ignore
                except AttributeError:
                    pass
            else:
                raise ValueError("No addition formula available.")
        else:
            return self.add(
                self.params.curve.prime, R, S, **self.params.curve.parameters  # type: ignore
            )[0]

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None or self.bits is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            half_bits = self.bits // 2
            r = self.rng(1 << half_bits)
            self.mults[0].init(self.params, self.point, half_bits)
            R = self.mults[0].multiply(int(r))  # r bounded by half_bits

            self.mults[1].init(self.params, self.point, half_bits)
            k1 = scalar % int(r)
            k2 = scalar // int(r)
            T = self.mults[1].multiply(k1)  # k1 bounded by half_bits

            self.mults[2].init(self.params, R, self.bits)
            S = self.mults[2].multiply(
                k2
            )  # k2 (in worst case) bounded by bits, but in practice closer to half_bits

            res = self._add(S, T)
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

    nmults = 1
    requires = set()

    def __init__(
        self,
        mult: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        rng: Callable[[int], Mod] = Mod.random,
    ):
        """
        :param mult: The multiplier to use.
        :param rng: The random number generator to use.
        """
        super().__init__(mult, rng=rng)

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None or self.bits is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            n = self.params.order
            self.mults[0].init(
                self.params,
                self.point,
                bits=max(self.bits, n.bit_length()) + 1,
            )
            scalar += n
            if scalar.bit_length() <= n.bit_length():
                scalar += n
            return action.exit(self.mults[0].multiply(scalar))


@public
class PointBlinding(ScalarMultiplierCountermeasure):
    """Point blinding countermeasure."""

    nmults = 2
    requires = {AdditionFormula, NegationFormula}
    add: Optional[AdditionFormula]
    neg: Optional[NegationFormula]

    def __init__(
        self,
        mult1: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        mult2: "ScalarMultiplier | ScalarMultiplierCountermeasure",
        rng: Callable[[int], Mod] = Mod.random,
        add: Optional[AdditionFormula] = None,
        neg: Optional[NegationFormula] = None,
    ):
        """

        :param mult1: The multiplier to use.
        :param mult2: The multiplier to use.
        :param rng: The random number generator to use.
        :param add: Addition formula to use, if None, the formula from the multiplier is used.
        :param neg: Negation formula to use, if None, the formula from the multiplier is used.
        """
        super().__init__(mult1, mult2, rng=rng)
        self.add = add
        self.neg = neg

    def multiply(self, scalar: int) -> Point:
        if self.params is None or self.point is None or self.bits is None:
            raise ValueError("Not initialized.")
        with ScalarMultiplicationAction(self.point, self.params, scalar) as action:
            R = self.params.curve.affine_random().to_model(
                self.params.curve.coordinate_model, self.params.curve
            )
            self.mults[0].init(self.params, R, self.bits)
            S = self.mults[0].multiply(int(scalar))

            T = self._add(self.point, R)
            self.mults[1].init(self.params, T, self.bits)
            Q = self.mults[1].multiply(int(scalar))

            return action.exit(self._add(Q, self._neg(S)))
