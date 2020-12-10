import random
import secrets
from functools import wraps, lru_cache
from abc import ABC, abstractmethod
from typing import Type

has_gmp = False
try:
    import gmpy2

    has_gmp = True
except ImportError:
    pass

from public import public

from .context import ResultAction


@public
def gcd(a, b):
    """Euclid's greatest common denominator algorithm."""
    if abs(a) < abs(b):
        return gcd(b, a)

    while abs(b) > 0:
        q, r = divmod(a, b)
        a, b = b, r

    return a


@public
def extgcd(a, b):
    """Extended Euclid's greatest common denominator algorithm."""
    if abs(b) > abs(a):
        (x, y, d) = extgcd(b, a)
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
@lru_cache
def miller_rabin(n: int, rounds: int = 50) -> bool:
    """Miller-Rabin probabilistic primality test."""
    if n == 2 or n == 3:
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
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def check(func):
    @wraps(func)
    def method(self, other):
        if type(self) is not type(other):
            other = self.__class__(other, self.n)
        else:
            if self.n != other.n:
                raise ValueError
        return func(self, other)

    return method


@public
class NonInvertibleError(ArithmeticError):
    pass


@public
class NonResidueError(ArithmeticError):
    pass


@public
class RandomModAction(ResultAction):
    """A random sampling from Z_n."""
    order: int

    def __init__(self, order: int):
        super().__init__()
        self.order = order

    def __repr__(self):
        return f"{self.__class__.__name__}({self.order:x})"


class BaseMod(ABC):
    def __init__(self, x, n):
        self.x = x
        self.n = n

    @check
    def __add__(self, other):
        return self.__class__((self.x + other.x) % self.n, self.n)

    @check
    def __radd__(self, other):
        return self + other

    @check
    def __sub__(self, other):
        return self.__class__((self.x - other.x) % self.n, self.n)

    @check
    def __rsub__(self, other):
        return -self + other

    def __neg__(self):
        return self.__class__(self.n - self.x, self.n)

    @abstractmethod
    def inverse(self):
        ...

    def __invert__(self):
        return self.inverse()

    @check
    def __mul__(self, other):
        return self.__class__((self.x * other.x) % self.n, self.n)

    @check
    def __rmul__(self, other):
        return self * other

    @check
    def __truediv__(self, other):
        return self * ~other

    @check
    def __rtruediv__(self, other):
        return ~self * other

    @check
    def __floordiv__(self, other):
        return self * ~other

    @check
    def __rfloordiv__(self, other):
        return ~self * other

    @check
    def __div__(self, other):
        return self.__floordiv__(other)

    @check
    def __rdiv__(self, other):
        return self.__rfloordiv__(other)

    @check
    def __divmod__(self, divisor):
        q, r = divmod(self.x, divisor.x)
        return self.__class__(q, self.n), self.__class__(r, self.n)

    @classmethod
    def random(cls, n: int):
        with RandomModAction(n) as action:
            return action.exit(cls(secrets.randbelow(n), n))


class RawMod(BaseMod):
    """An element x of ℤₙ."""
    x: int
    n: int

    def __init__(self, x: int, n: int):
        super().__init__(x % n, n)

    def inverse(self):
        if self.x == 0:
            raise NonInvertibleError("Inverting zero.")
        x, y, d = extgcd(self.x, self.n)
        if d != 1:
            raise NonInvertibleError("Element not invertible.")
        return RawMod(x, self.n)

    def is_residue(self):
        """Whether this element is a quadratic residue (only implemented for prime modulus)."""
        if not miller_rabin(self.n):
            raise NotImplementedError
        if self.x == 0:
            return True
        if self.n == 2:
            return self.x in (0, 1)
        legendre_symbol = self ** ((self.n - 1) // 2)
        return legendre_symbol == 1

    def sqrt(self):
        """
        The modular square root of this element (only implemented for prime modulus).

        Uses the `Tonelli-Shanks <https://en.wikipedia.org/wiki/Tonelli–Shanks_algorithm>`_ algorithm.
        """
        if not miller_rabin(self.n):
            raise NotImplementedError
        if not self.is_residue():
            if self.x == 0:
                return RawMod(0, self.n)
            else:
                raise NonResidueError("No square root exists.")
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

    def __pow__(self, n):
        if type(n) is not int:
            raise TypeError
        if n == 0:
            return RawMod(1, self.n)
        if n < 0:
            return self.inverse() ** (-n)
        if n == 1:
            return RawMod(self.x, self.n)

        return RawMod(pow(self.x, n, self.n), self.n)


@public
class Undefined(BaseMod):
    def __init__(self):
        super().__init__(None, None)

    def __add__(self, other):
        raise NotImplementedError

    def __radd__(self, other):
        raise NotImplementedError

    def __sub__(self, other):
        raise NotImplementedError

    def __rsub__(self, other):
        raise NotImplementedError

    def __neg__(self):
        raise NotImplementedError

    def inverse(self):
        raise NotImplementedError

    def __invert__(self):
        raise NotImplementedError

    def __mul__(self, other):
        raise NotImplementedError

    def __rmul__(self, other):
        raise NotImplementedError

    def __truediv__(self, other):
        raise NotImplementedError

    def __rtruediv__(self, other):
        raise NotImplementedError

    def __floordiv__(self, other):
        raise NotImplementedError

    def __rfloordiv__(self, other):
        raise NotImplementedError

    def __div__(self, other):
        raise NotImplementedError

    def __rdiv__(self, other):
        raise NotImplementedError

    def __divmod__(self, divisor):
        raise NotImplementedError

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

    def __pow__(self, n):
        raise NotImplementedError


if has_gmp:

    class GMPMod(BaseMod):
        """An element x of ℤₙ. Implemented by GMP."""
        x: gmpy2.mpz
        n: gmpy2.mpz

        def __init__(self, x: int, n: int):
            super().__init__(gmpy2.mpz(x % n), gmpy2.mpz(n))

        def inverse(self):
            if self.x == 0:
                raise NonInvertibleError("Inverting zero!")
            if self.x == 1:
                return GMPMod(1, self.n)
            try:
                res = gmpy2.invert(self.x, self.n)
            except ZeroDivisionError:
                raise NonInvertibleError("Element not invertible.")
            return GMPMod(res, self.n)

        def is_residue(self):
            """Whether this element is a quadratic residue (only implemented for prime modulus)."""
            if not gmpy2.is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return True
            if self.n == 2:
                return self.x in (0, 1)
            return gmpy2.legendre(self.x, self.n) == 1

        def sqrt(self):
            """
            The modular square root of this element (only implemented for prime modulus).

            Uses the `Tonelli-Shanks <https://en.wikipedia.org/wiki/Tonelli–Shanks_algorithm>`_ algorithm.
            """
            if not gmpy2.is_prime(self.n):
                raise NotImplementedError
            if not self.is_residue():
                if self.x == 0:
                    return GMPMod(0, self.n)
                else:
                    raise NonResidueError("No square root exists.")
            if self.n % 4 == 3:
                return self ** int((self.n + 1) // 4)
            q = self.n - 1
            s = 0
            while q % 2 == 0:
                q //= 2
                s += 1

            z = 2
            while GMPMod(z, self.n).is_residue():
                z += 1

            m = s
            c = GMPMod(z, self.n) ** int(q)
            t = self ** int(q)
            r_exp = (q + 1) // 2
            r = self ** int(r_exp)

            while t != 1:
                i = 1
                while not (t ** (2 ** i)) == 1:
                    i += 1
                two_exp = m - (i + 1)
                b = c ** int(GMPMod(2, self.n) ** two_exp)
                m = int(GMPMod(i, self.n))
                c = b ** 2
                t *= c
                r *= b
            return r

        @check
        def __divmod__(self, divisor):
            q, r = gmpy2.f_divmod(self.x, divisor.x)
            return GMPMod(q, self.n), GMPMod(r, self.n)

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

        def __pow__(self, n):
            if type(n) not in (int, gmpy2.mpz):
                raise TypeError
            if n == 0:
                return GMPMod(1, self.n)
            if n < 0:
                return self.inverse() ** (-n)
            if n == 1:
                return GMPMod(self.x, self.n)
            return GMPMod(gmpy2.powmod(self.x, gmpy2.mpz(n), self.n), self.n)

    Mod = GMPMod
else:
    Mod = RawMod

public(Mod=Mod)
