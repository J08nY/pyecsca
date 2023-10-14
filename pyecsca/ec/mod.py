"""
Provides several implementations of an element of ℤₙ.

The base class :py:class:`Mod` dynamically
dispatches to the implementation chosen by the runtime configuration of the library
(see :py:class:`pyecsca.misc.cfg.Config`). A Python integer based implementation is available under
:py:class:`RawMod`. A symbolic implementation based on sympy is available under :py:class:`SymbolicMod`. If
`gmpy2` is installed, a GMP based implementation is available under :py:class:`GMPMod`.
"""
import random
import secrets
from functools import wraps, lru_cache
from typing import Type, Dict, Any, Tuple, Union

from public import public
from sympy import Expr, FF

from .error import raise_non_invertible, raise_non_residue
from .context import ResultAction
from ..misc.cfg import getconfig

has_gmp = False
try:
    import gmpy2

    has_gmp = True
except ImportError:
    gmpy2 = None


@public
def gcd(a, b):
    """Euclid's greatest common denominator algorithm."""
    if abs(a) < abs(b):
        return gcd(b, a)

    while abs(b) > 0:
        _, r = divmod(a, b)
        a, b = b, r

    return a


@public
def extgcd(a, b):
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


@public
class Mod:
    """An element x of ℤₙ."""

    x: Any
    n: Any
    __slots__ = ("x", "n")

    def __new__(cls, *args, **kwargs) -> "Mod":
        if cls != Mod:
            return cls.__new__(cls, *args, **kwargs)
        if not _mod_classes:
            raise ValueError("Cannot find any working Mod class.")
        selected_class = getconfig().ec.mod_implementation
        if selected_class not in _mod_classes:
            # Fallback to something
            selected_class = next(iter(_mod_classes.keys()))
        return _mod_classes[selected_class].__new__(
            _mod_classes[selected_class], *args, **kwargs
        )

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

    @_check
    def __divmod__(self, divisor) -> Tuple["Mod", "Mod"]:
        q, r = divmod(self.x, divisor.x)
        return self.__class__(q, self.n), self.__class__(r, self.n)

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
            return action.exit(cls(secrets.randbelow(n), n))

    def __pow__(self, n) -> "Mod":
        return NotImplemented

    def __str__(self):
        return str(self.x)


@public
class RawMod(Mod):
    """An element x of ℤₙ (implemented using Python integers)."""

    x: int
    n: int
    __slots__ = ("x", "n")

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, x: int, n: int):
        self.x = x % n
        self.n = n

    def inverse(self) -> "RawMod":
        if self.x == 0:
            raise_non_invertible()
        x, _, d = extgcd(self.x, self.n)
        if d != 1:
            raise_non_invertible()
        return RawMod(x, self.n)

    def is_residue(self):
        if not miller_rabin(self.n):
            raise NotImplementedError
        if self.x == 0:
            return True
        if self.n == 2:
            return self.x in (0, 1)
        legendre_symbol = jacobi(self.x, self.n)
        return legendre_symbol == 1

    def sqrt(self) -> "RawMod":
        if not miller_rabin(self.n):
            raise NotImplementedError
        if self.x == 0:
            return RawMod(0, self.n)
        if not self.is_residue():
            raise_non_residue()
        if self.n % 4 == 3:
            return self ** int((self.n + 1) // 4)
        q = self.n - 1
        s = 0
        while q % 2 == 0:
            q //= 2
            s += 1

        z = 2
        while RawMod(z, self.n).is_residue():
            z += 1

        m = s
        c = RawMod(z, self.n) ** q
        t = self ** q
        r_exp = (q + 1) // 2
        r = self ** r_exp

        while t != 1:
            i = 1
            while not (t ** (2 ** i)) == 1:
                i += 1
            two_exp = m - (i + 1)
            b = c ** int(RawMod(2, self.n) ** two_exp)
            m = int(RawMod(i, self.n))
            c = b ** 2
            t *= c
            r *= b
        return r

    def __bytes__(self):
        return self.x.to_bytes((self.n.bit_length() + 7) // 8, byteorder="big")

    def __int__(self):
        return self.x

    def __eq__(self, other):
        if type(other) is int:
            return self.x == (other % self.n)
        if type(other) is not RawMod:
            return False
        return self.x == other.x and self.n == other.n

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return str(self.x)

    def __hash__(self):
        return hash(("RawMod", self.x, self.n))

    def __pow__(self, n) -> "RawMod":
        if type(n) is not int:
            raise TypeError
        if n == 0:
            return RawMod(1, self.n)
        if n < 0:
            return self.inverse() ** (-n)
        if n == 1:
            return RawMod(self.x, self.n)

        return RawMod(pow(self.x, n, self.n), self.n)


_mod_classes["python"] = RawMod


@public
class Undefined(Mod):
    """A special undefined element."""
    __slots__ = ("x", "n")

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

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

    def __divmod__(self, divisor):
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

    def __pow__(self, n):
        return NotImplemented


@lru_cache
def __ff_cache(n):
    return FF(n)


def _symbolic_check(func):
    @wraps(func)
    def method(self, other):
        if type(self) is not type(other):
            if type(other) is int:
                other = self.__class__(__ff_cache(self.n)(other), self.n)
            else:
                other = self.__class__(other, self.n)
        else:
            if self.n != other.n:
                raise ValueError
        return func(self, other)

    return method


@public
class SymbolicMod(Mod):
    """A symbolic element x of ℤₙ (implemented using sympy)."""

    x: Expr
    n: int
    __slots__ = ("x", "n")

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self, x: Expr, n: int):
        self.x = x
        self.n = n

    @_symbolic_check
    def __add__(self, other) -> "SymbolicMod":
        return self.__class__((self.x + other.x), self.n)

    @_symbolic_check
    def __radd__(self, other) -> "SymbolicMod":
        return self + other

    @_symbolic_check
    def __sub__(self, other) -> "SymbolicMod":
        return self.__class__((self.x - other.x), self.n)

    @_symbolic_check
    def __rsub__(self, other) -> "SymbolicMod":
        return -self + other

    def __neg__(self) -> "SymbolicMod":
        return self.__class__(-self.x, self.n)

    def inverse(self) -> "SymbolicMod":
        return self.__class__(self.x ** (-1), self.n)

    def sqrt(self) -> "SymbolicMod":
        raise NotImplementedError

    def is_residue(self):
        raise NotImplementedError

    def __invert__(self) -> "SymbolicMod":
        return self.inverse()

    @_symbolic_check
    def __mul__(self, other) -> "SymbolicMod":
        return self.__class__(self.x * other.x, self.n)

    @_symbolic_check
    def __rmul__(self, other) -> "SymbolicMod":
        return self * other

    @_symbolic_check
    def __truediv__(self, other) -> "SymbolicMod":
        return self * ~other

    @_symbolic_check
    def __rtruediv__(self, other) -> "SymbolicMod":
        return ~self * other

    @_symbolic_check
    def __floordiv__(self, other) -> "SymbolicMod":
        return self * ~other

    @_symbolic_check
    def __rfloordiv__(self, other) -> "SymbolicMod":
        return ~self * other

    def __divmod__(self, divisor) -> "SymbolicMod":
        return NotImplemented

    def __bytes__(self):
        return int(self.x).to_bytes((self.n.bit_length() + 7) // 8, byteorder="big")

    def __int__(self):
        return int(self.x)

    def __eq__(self, other):
        if type(other) is int:
            return self.x == other % self.n
        if type(other) is not SymbolicMod:
            return False
        return self.x == other.x and self.n == other.n

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return str(self.x)

    def __hash__(self):
        return hash(("SymbolicMod", self.x, self.n))

    def __pow__(self, n) -> "SymbolicMod":
        return self.__class__(pow(self.x, n), self.n)


_mod_classes["symbolic"] = SymbolicMod

if has_gmp:

    @lru_cache
    def _is_prime(x) -> bool:
        return gmpy2.is_prime(x)

    @public
    class GMPMod(Mod):
        """An element x of ℤₙ. Implemented by GMP."""

        x: gmpy2.mpz
        n: gmpy2.mpz
        __slots__ = ("x", "n")

        def __new__(cls, *args, **kwargs):
            return object.__new__(cls)

        def __init__(self, x: Union[int, gmpy2.mpz], n: Union[int, gmpy2.mpz], ensure: bool = True):
            if ensure:
                self.n = gmpy2.mpz(n)
                self.x = gmpy2.mpz(x % self.n)
            else:
                self.n = n
                self.x = x

        def inverse(self) -> "GMPMod":
            if self.x == 0:
                raise_non_invertible()
            if self.x == 1:
                return GMPMod(gmpy2.mpz(1), self.n, ensure=False)
            try:
                res = gmpy2.invert(self.x, self.n)
            except ZeroDivisionError:
                raise_non_invertible()
                res = gmpy2.mpz(0)
            return GMPMod(res, self.n, ensure=False)

        def is_residue(self) -> bool:
            if not _is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return True
            if self.n == 2:
                return self.x in (0, 1)
            return gmpy2.legendre(self.x, self.n) == 1

        def sqrt(self) -> "GMPMod":
            if not _is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return GMPMod(gmpy2.mpz(0), self.n, ensure=False)
            if not self.is_residue():
                raise_non_residue()
            if self.n % 4 == 3:
                return self ** int((self.n + 1) // 4)
            q = self.n - 1
            s = 0
            while q % 2 == 0:
                q //= 2
                s += 1

            z = gmpy2.mpz(2)
            while GMPMod(z, self.n, ensure=False).is_residue():
                z += 1

            m = s
            c = GMPMod(z, self.n, ensure=False) ** int(q)
            t = self ** int(q)
            r_exp = (q + 1) // 2
            r = self ** int(r_exp)

            while t != 1:
                i = 1
                while not (t ** (2 ** i)) == 1:
                    i += 1
                two_exp = m - (i + 1)
                b = c ** int(GMPMod(gmpy2.mpz(2), self.n, ensure=False) ** two_exp)
                m = int(GMPMod(gmpy2.mpz(i), self.n, ensure=False))
                c = b ** 2
                t *= c
                r *= b
            return r

        @_check
        def __add__(self, other) -> "GMPMod":
            return GMPMod((self.x + other.x) % self.n, self.n, ensure=False)

        @_check
        def __sub__(self, other) -> "GMPMod":
            return GMPMod((self.x - other.x) % self.n, self.n, ensure=False)

        def __neg__(self) -> "GMPMod":
            return GMPMod(self.n - self.x, self.n, ensure=False)

        @_check
        def __mul__(self, other) -> "GMPMod":
            return GMPMod((self.x * other.x) % self.n, self.n, ensure=False)

        @_check
        def __divmod__(self, divisor) -> Tuple["GMPMod", "GMPMod"]:
            q, r = gmpy2.f_divmod(self.x, divisor.x)
            return GMPMod(q, self.n, ensure=False), GMPMod(r, self.n, ensure=False)

        def __bytes__(self):
            return int(self.x).to_bytes((self.n.bit_length() + 7) // 8, byteorder="big")

        def __int__(self):
            return int(self.x)

        def __eq__(self, other):
            if type(other) is int:
                return self.x == (gmpy2.mpz(other) % self.n)
            if type(other) is not GMPMod:
                return False
            return self.x == other.x and self.n == other.n

        def __ne__(self, other):
            return not self == other

        def __repr__(self):
            return str(int(self.x))

        def __hash__(self):
            return hash(("GMPMod", self.x, self.n))

        def __pow__(self, n) -> "GMPMod":
            if type(n) not in (int, gmpy2.mpz):
                raise TypeError
            if n == 0:
                return GMPMod(gmpy2.mpz(1), self.n, ensure=False)
            if n < 0:
                return self.inverse() ** (-n)
            if n == 1:
                return GMPMod(self.x, self.n, ensure=False)
            return GMPMod(gmpy2.powmod(self.x, gmpy2.mpz(n), self.n), self.n, ensure=False)

    _mod_classes["gmp"] = GMPMod
