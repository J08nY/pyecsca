"""
Provides several implementations of an element of ℤₙ.

The base class :py:class:`Mod` dynamically
dispatches to the implementation chosen by the runtime configuration of the library
(see :py:class:`pyecsca.misc.cfg.Config`). A Python integer based implementation is available under
:py:class:`RawMod`. A symbolic implementation based on sympy is available under :py:class:`SymbolicMod`. If
`gmpy2` is installed, a GMP based implementation is available under :py:class:`GMPMod`. If `python-flint` is
installed, a flint based implementation is available under :py:class:`FlintMod`.
"""
import random
import secrets
import warnings
from functools import wraps, lru_cache
from typing import Type, Dict, Any, Tuple, Union

from public import public
from sympy import Expr

from pyecsca.ec.error import (
    raise_non_invertible,
    raise_non_residue,
    NonResidueError,
    NonResidueWarning,
)
from pyecsca.ec.context import ResultAction
from pyecsca.misc.cfg import getconfig

has_gmp = False
try:
    import gmpy2

    has_gmp = True
except ImportError:
    gmpy2 = None


has_flint = False
try:
    import flint

    _major, _minor, *_ = flint.__version__.split(".")
    if (int(_major), int(_minor)) >= (0, 5):
        has_flint = True
    else:
        flint = None
except ImportError:
    flint = None


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

    >>> a = Mod(3, 5)
    >>> b = Mod(2, 5)
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

    def __new__(cls, *args, **kwargs) -> "Mod":
        if cls != Mod:
            return cls.__new__(cls, *args, **kwargs)
        if not _mod_classes:
            raise ValueError("Cannot find any working Mod class.")
        selected_class = getconfig().ec.mod_implementation
        if selected_class not in _mod_classes:
            # Fallback to something
            for fallback in _mod_order:
                if fallback in _mod_classes:
                    selected_class = fallback
                    break
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

    def bit_length(self):
        return self.x.bit_length()

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
        t = self**q
        r_exp = (q + 1) // 2
        r = self**r_exp

        while t != 1:
            i = 1
            while not (t ** (2**i)) == 1:
                i += 1
            two_exp = m - (i + 1)
            b = c ** int(RawMod(2, self.n) ** two_exp)
            m = int(RawMod(i, self.n))
            c = b**2
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

    def __pow__(self, n):
        return NotImplemented


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

    @_check
    def __add__(self, other) -> "SymbolicMod":
        return self.__class__((self.x + other.x), self.n)

    @_check
    def __radd__(self, other) -> "SymbolicMod":
        return self + other

    @_check
    def __sub__(self, other) -> "SymbolicMod":
        return self.__class__((self.x - other.x), self.n)

    @_check
    def __rsub__(self, other) -> "SymbolicMod":
        return -self + other

    def __neg__(self) -> "SymbolicMod":
        return self.__class__(-self.x, self.n)

    def bit_length(self):
        raise NotImplementedError

    def inverse(self) -> "SymbolicMod":
        return self.__class__(self.x ** (-1), self.n)

    def sqrt(self) -> "SymbolicMod":
        raise NotImplementedError

    def is_residue(self):
        raise NotImplementedError

    def __invert__(self) -> "SymbolicMod":
        return self.inverse()

    @_check
    def __mul__(self, other) -> "SymbolicMod":
        return self.__class__(self.x * other.x, self.n)

    @_check
    def __rmul__(self, other) -> "SymbolicMod":
        return self * other

    @_check
    def __truediv__(self, other) -> "SymbolicMod":
        return self * ~other

    @_check
    def __rtruediv__(self, other) -> "SymbolicMod":
        return ~self * other

    @_check
    def __floordiv__(self, other) -> "SymbolicMod":
        return self * ~other

    @_check
    def __rfloordiv__(self, other) -> "SymbolicMod":
        return ~self * other

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
    def _gmpy_is_prime(x) -> bool:
        return gmpy2.is_prime(x)

    @public
    class GMPMod(Mod):
        """An element x of ℤₙ. Implemented by GMP."""

        x: gmpy2.mpz
        n: gmpy2.mpz
        __slots__ = ("x", "n")

        def __new__(cls, *args, **kwargs):
            return object.__new__(cls)

        def __init__(
            self,
            x: Union[int, gmpy2.mpz],
            n: Union[int, gmpy2.mpz],
            ensure: bool = True,
        ):
            if ensure:
                self.n = gmpy2.mpz(n)
                self.x = gmpy2.mpz(x % self.n)
            else:
                self.n = n
                self.x = x

        def bit_length(self):
            return self.x.bit_length()

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
            if not _gmpy_is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return True
            if self.n == 2:
                return self.x in (0, 1)
            return gmpy2.legendre(self.x, self.n) == 1

        def sqrt(self) -> "GMPMod":
            if not _gmpy_is_prime(self.n):
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
                while not (t ** (2**i)) == 1:
                    i += 1
                two_exp = m - (i + 1)
                b = c ** int(GMPMod(gmpy2.mpz(2), self.n, ensure=False) ** two_exp)
                m = int(GMPMod(gmpy2.mpz(i), self.n, ensure=False))
                c = b**2
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
            return GMPMod(
                gmpy2.powmod(self.x, gmpy2.mpz(n), self.n), self.n, ensure=False
            )

    _mod_classes["gmp"] = GMPMod


if has_flint:

    @lru_cache
    def _fmpz_ctx(n: Union[int, flint.fmpz_mod_ctx]) -> flint.fmpz_mod_ctx:
        if type(n) is flint.fmpz_mod_ctx:
            return n
        return flint.fmpz_mod_ctx(n)

    @lru_cache
    def _fmpz_is_prime(x: flint.fmpz) -> bool:
        return x.is_probable_prime()

    def _flint_check(func):
        @wraps(func)
        def method(self, other):
            if self.__class__ is not type(other):
                other = self.__class__(other, self.n)
            elif self._ctx != other._ctx:
                raise ValueError
            return func(self, other)

        return method

    @public
    class FlintMod(Mod):
        """An element x of ℤₙ. Implemented by flint."""

        x: flint.fmpz_mod
        _ctx: flint.fmpz_mod_ctx
        __slots__ = ("x", "_ctx")

        def __new__(cls, *args, **kwargs):
            return object.__new__(cls)

        def __init__(
            self,
            x: Union[int, flint.fmpz_mod],
            n: Union[int, flint.fmpz_mod_ctx],
            ensure: bool = True,
        ):
            if ensure:
                self._ctx = _fmpz_ctx(n)
                self.x = self._ctx(x)
            else:
                self._ctx = n
                self.x = x

        @property
        def n(self) -> flint.fmpz:
            return self._ctx.modulus()

        def bit_length(self):
            return int(self.x).bit_length()

        def inverse(self) -> "FlintMod":
            if self.x == 0:
                raise_non_invertible()
            if self.x == 1:
                return FlintMod(self._ctx(1), self._ctx, ensure=False)
            try:
                res = self.x.inverse()
            except ZeroDivisionError:
                raise_non_invertible()
                res = self._ctx(0)
            return FlintMod(res, self._ctx, ensure=False)

        def is_residue(self) -> bool:
            try:
                with warnings.catch_warnings(record=True) as warns:
                    self.sqrt()
                if warns and isinstance(warns[0], NonResidueWarning):
                    return False
            except NonResidueError:
                return False
            return True

        def sqrt(self) -> "FlintMod":
            mod = self.n
            if not _fmpz_is_prime(mod):
                raise NotImplementedError
            try:
                res = flint.fmpz(int(self.x)).sqrtmod(mod)
                return FlintMod(self._ctx(res), self._ctx, ensure=False)
            except ValueError:
                raise_non_residue()

            if mod % 4 == 3:
                return self ** int((mod + 1) // 4)
            q = mod - 1
            s = 0
            while q % 2 == 0:
                q //= 2
                s += 1

            z = self._ctx(2)
            while FlintMod(z, self._ctx, ensure=False).is_residue():
                z += 1

            m = s
            c = FlintMod(z, self._ctx, ensure=False) ** int(q)
            t = self ** int(q)
            r_exp = (q + 1) // 2
            r = self ** int(r_exp)

            while t != 1:
                i = 1
                while not (t ** (2**i)) == 1:
                    i += 1
                two_exp = m - (i + 1)
                b = c ** int(FlintMod(self._ctx(2), self._ctx, ensure=False) ** two_exp)
                m = int(FlintMod(self._ctx(i), self._ctx, ensure=False))
                c = b**2
                t *= c
                r *= b
            return r

        @_flint_check
        def __add__(self, other) -> "FlintMod":
            return FlintMod(self.x + other.x, self._ctx, ensure=False)

        @_flint_check
        def __radd__(self, other) -> "Mod":
            return self + other

        @_flint_check
        def __sub__(self, other) -> "FlintMod":
            return FlintMod(self.x - other.x, self._ctx, ensure=False)

        @_flint_check
        def __rsub__(self, other) -> "Mod":
            return -self + other

        def __neg__(self) -> "FlintMod":
            return FlintMod(-self.x, self._ctx, ensure=False)

        @_flint_check
        def __mul__(self, other) -> "FlintMod":
            return FlintMod(self.x * other.x, self._ctx, ensure=False)

        @_flint_check
        def __rmul__(self, other) -> "Mod":
            return self * other

        @_flint_check
        def __truediv__(self, other) -> "Mod":
            return self * ~other

        @_flint_check
        def __rtruediv__(self, other) -> "Mod":
            return ~self * other

        @_flint_check
        def __floordiv__(self, other) -> "Mod":
            return self * ~other

        @_flint_check
        def __rfloordiv__(self, other) -> "Mod":
            return ~self * other

        def __bytes__(self):
            return int(self.x).to_bytes(
                (int(self.n).bit_length() + 7) // 8, byteorder="big"
            )

        def __int__(self):
            return int(self.x)

        def __eq__(self, other):
            if type(other) is int:
                return self.x == other
            if type(other) is not FlintMod:
                return False
            try:
                return self.x == other.x
            except ValueError:
                return False

        def __ne__(self, other):
            return not self == other

        def __repr__(self):
            return str(int(self.x))

        def __hash__(self):
            return hash(("FlintMod", self.x, self.n))

        def __pow__(self, n) -> "FlintMod":
            if type(n) not in (int, flint.fmpz):
                raise TypeError
            if n == 0:
                return FlintMod(self._ctx(1), self._ctx, ensure=False)
            if n < 0:
                return self.inverse() ** (-n)
            if n == 1:
                return FlintMod(self.x, self._ctx, ensure=False)
            return FlintMod(self.x**n, self._ctx, ensure=False)

        def __getstate__(self):
            return {"x": int(self.x), "n": int(self.n)}

        def __setstate__(self, state):
            self._ctx = _fmpz_ctx(state["n"])
            self.x = self._ctx(state["x"])

    _mod_classes["flint"] = FlintMod
