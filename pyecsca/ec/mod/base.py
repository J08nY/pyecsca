import random
import secrets
from functools import lru_cache, wraps

from public import public
from typing import Tuple, Any, Dict, Type

from pyecsca.ec.context import ResultAction
from pyecsca.misc.cfg import getconfig


@public
def gcd(a: int, b: int) -> int:
    """Euclid's greatest common denominator algorithm."""
    if abs(a) < abs(b):
        return gcd(b, a)

    while abs(b) > 0:
        _, r = divmod(a, b)
        a, b = b, r

    return a


@public
def extgcd(a: int, b: int) -> Tuple[int, int, int]:
    """Compute the extended Euclid's greatest common denominator algorithm."""
    if abs(b) > abs(a):
        x, y, d = extgcd(b, a)
        return y, x, d

    if abs(b) == 0:
        return 1, 0, a

    x1, x2, y1, y2 = 0, 1, 1, 0
    while abs(b) > 0:
        q, r = divmod(a, b)
        x = x2 - q * x1
        y = y2 - q * y1
        a, b, x2, x1, y2, y1 = b, r, x1, x, y1, y

    return x2, y2, a


@public
def jacobi(x: int, n: int) -> int:
    """Jacobi symbol."""
    if n <= 0:
        raise ValueError("'n' must be a positive integer.")
    if n % 2 == 0:
        raise ValueError("'n' must be odd.")
    x %= n
    r = 1
    while x != 0:
        while x % 2 == 0:
            x //= 2
            nm8 = n % 8
            if nm8 in (3, 5):
                r = -r
        x, n = n, x
        if x % 4 == 3 and n % 4 == 3:
            r = -r
        x %= n
    return r if n == 1 else 0


@public
@lru_cache
def miller_rabin(n: int, rounds: int = 50) -> bool:
    """Miller-Rabin probabilistic primality test."""
    if n in (2, 3):
        return True

    if n % 2 == 0:
        return False

    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2
    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, s, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _check(func):
    @wraps(func)
    def method(self, other):
        if self.__class__ is not type(other):
            other = self.__class__(other, self.n)
        elif self.n != other.n:
            raise ValueError
        return func(self, other)

    return method


@public
class RandomModAction(ResultAction):
    """A random sampling from Z_n."""

    order: int

    def __init__(self, order: int):
        super().__init__()
        self.order = order

    def __repr__(self):
        return f"{self.__class__.__name__}({self.order:x})"


_mod_classes: Dict[str, Type] = {}
_mod_order = ["gmp", "flint", "python"]


@public
class Mod:
    """
    An element x of ℤₙ.

    .. note::
        This class dispatches to one of :py:class:`RawMod`, :py:class:`GMPMod` or :py:class:`FlintMod`
        based on what packages are installed and what implementation is configured (see
        :py:mod:`pyecsca.misc.cfg`).

    Has all the usual special methods that upcast integers automatically:

    >>> a = mod(3, 5)
    >>> b = mod(2, 5)
    >>> a + b
    0
    >>> a * 2
    1
    >>> a == 3
    True
    >>> a == -2
    True
    >>> -a
    2

    Plus some additional useful things:

    >>> a.inverse()
    2
    >>> a.is_residue()
    False
    >>> (a**2).is_residue()
    True
    >>> (a**2).sqrt() in (a, -a)
    True
    """

    x: Any
    n: Any
    __slots__ = ("x", "n")

    def __init__(self, x, n):
        raise TypeError("Abstract")

    @_check
    def __add__(self, other) -> "Mod":
        return self.__class__((self.x + other.x) % self.n, self.n)

    @_check
    def __radd__(self, other) -> "Mod":
        return self + other

    @_check
    def __sub__(self, other) -> "Mod":
        return self.__class__((self.x - other.x) % self.n, self.n)

    @_check
    def __rsub__(self, other) -> "Mod":
        return -self + other

    def __neg__(self) -> "Mod":
        return self.__class__(self.n - self.x, self.n)

    def bit_length(self):
        """
        Compute the bit length of this element (in its positive integer representation).

        :return: The bit-length.
        """
        raise NotImplementedError

    def inverse(self) -> "Mod":
        """
        Invert the element.

        :return: The inverse.
        :raises: :py:class:`NonInvertibleError` if the element is not invertible.
        """
        raise NotImplementedError

    def __invert__(self) -> "Mod":
        return self.inverse()

    def is_residue(self) -> bool:
        """Whether this element is a quadratic residue (only implemented for prime modulus)."""
        raise NotImplementedError

    def sqrt(self) -> "Mod":
        """
        Compute the modular square root of this element (only implemented for prime modulus).

        Uses the `Tonelli-Shanks <https://en.wikipedia.org/wiki/Tonelli–Shanks_algorithm>`_ algorithm.
        """
        raise NotImplementedError

    @_check
    def __mul__(self, other) -> "Mod":
        return self.__class__((self.x * other.x) % self.n, self.n)

    @_check
    def __rmul__(self, other) -> "Mod":
        return self * other

    @_check
    def __truediv__(self, other) -> "Mod":
        return self * ~other

    @_check
    def __rtruediv__(self, other) -> "Mod":
        return ~self * other

    @_check
    def __floordiv__(self, other) -> "Mod":
        return self * ~other

    @_check
    def __rfloordiv__(self, other) -> "Mod":
        return ~self * other

    def __bytes__(self) -> bytes:
        raise NotImplementedError

    def __int__(self) -> int:
        raise NotImplementedError

    @classmethod
    def random(cls, n: int) -> "Mod":
        """
        Generate a random :py:class:`Mod` in ℤₙ.

        :param n: The order.
        :return: The random :py:class:`Mod`.
        """
        with RandomModAction(n) as action:
            return action.exit(mod(secrets.randbelow(n), n))

    def __pow__(self, n, _=None) -> "Mod":
        return NotImplemented

    def __str__(self):
        return str(self.x)


@public
class Undefined(Mod):
    """A special undefined element."""

    __slots__ = ("x", "n")

    def __init__(self):
        self.x = None
        self.n = None

    def __add__(self, other):
        return NotImplemented

    def __radd__(self, other):
        return NotImplemented

    def __sub__(self, other):
        return NotImplemented

    def __rsub__(self, other):
        return NotImplemented

    def __neg__(self):
        raise NotImplementedError

    def bit_length(self):
        raise NotImplementedError

    def inverse(self):
        raise NotImplementedError

    def sqrt(self):
        raise NotImplementedError

    def is_residue(self):
        raise NotImplementedError

    def __invert__(self):
        raise NotImplementedError

    def __mul__(self, other):
        return NotImplemented

    def __rmul__(self, other):
        return NotImplemented

    def __truediv__(self, other):
        return NotImplemented

    def __rtruediv__(self, other):
        return NotImplemented

    def __floordiv__(self, other):
        return NotImplemented

    def __rfloordiv__(self, other):
        return NotImplemented

    def __bytes__(self):
        raise NotImplementedError

    def __int__(self):
        raise NotImplementedError

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return False

    def __repr__(self):
        return "Undefined"

    def __hash__(self):
        return hash("Undefined") + 1

    def __pow__(self, n, _=None):
        return NotImplemented


@public
def mod(x: int, n: int) -> Mod:
    """
    Construct a :py:class:`Mod`.

    :param x: The value.
    :param n: The modulus.
    :return: A selected Mod implementation object.
    :raises: ValueError in case a working Mod implementation cannot be found.
    """
    if not _mod_classes:
        raise ValueError("Cannot find any working Mod class.")
    selected_class = getconfig().ec.mod_implementation
    if selected_class not in _mod_classes:
        # Fallback to something
        for fallback in _mod_order:
            if fallback in _mod_classes:
                selected_class = fallback
                break
    return _mod_classes[selected_class](x, n)
