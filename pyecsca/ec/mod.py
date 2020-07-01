import random
import secrets
from functools import wraps, lru_cache

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
class RandomModAction(ResultAction):
    """A random sampling from Z_n."""
    order: int

    def __init__(self, order: int):
        super().__init__()
        self.order = order

    def __repr__(self):
        return f"{self.__class__.__name__}({self.order:x})"


@public
class Mod(object):
    """An element x of ℤₙ."""

    def __init__(self, x: int, n: int):
        self.x: int = x % n
        self.n: int = n

    @check
    def __add__(self, other):
        return Mod((self.x + other.x) % self.n, self.n)

    @check
    def __radd__(self, other):
        return self + other

    @check
    def __sub__(self, other):
        return Mod((self.x - other.x) % self.n, self.n)

    @check
    def __rsub__(self, other):
        return -self + other

    def __neg__(self):
        return Mod(self.n - self.x, self.n)

    def inverse(self):
        x, y, d = extgcd(self.x, self.n)
        return Mod(x, self.n)

    def __invert__(self):
        return self.inverse()

    def is_residue(self):
        """Whether this element is a quadratic residue (only implemented for prime modulus)."""
        if not miller_rabin(self.n):
            raise NotImplementedError
        if self.x == 0:
            return True
        if self.n == 2:
            return self.x in (0, 1)
        legendre = self ** ((self.n - 1) // 2)
        return legendre == 1

    def sqrt(self):
        """
        The modular square root of this element (only implemented for prime modulus).

        Uses the `Tonelli-Shanks <https://en.wikipedia.org/wiki/Tonelli–Shanks_algorithm>`_ algorithm.
        """
        if not miller_rabin(self.n):
            raise NotImplementedError
        q = self.n - 1
        s = 0
        while q % 2 == 0:
            q //= 2
            s += 1

        z = 2
        while Mod(z, self.n).is_residue():
            z += 1

        m = s
        c = Mod(z, self.n) ** q
        t = self ** q
        r_exp = (q + 1) // 2
        r = self ** r_exp

        while t != 1:
            i = 1
            while not (t ** (2**i)) == 1:
                i += 1
            two_exp = m - (i + 1)
            b = c ** int(Mod(2, self.n)**two_exp)
            m = int(Mod(i, self.n))
            c = b ** 2
            t *= c
            r *= b
        return r

    @check
    def __mul__(self, other):
        return Mod((self.x * other.x) % self.n, self.n)

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
        return Mod(q, self.n), Mod(r, self.n)

    def __bytes__(self):
        return self.x.to_bytes((self.n.bit_length() + 7) // 8, byteorder="big")

    @staticmethod
    def random(n: int):
        with RandomModAction(n) as action:
            return action.exit(Mod(secrets.randbelow(n), n))

    def __int__(self):
        return self.x

    def __eq__(self, other):
        if type(other) is int:
            return self.x == (other % self.n)
        if type(other) is not Mod:
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
            return Mod(1, self.n)
        if n < 0:
            return self.inverse()**(-n)
        if n == 1:
            return Mod(self.x, self.n)

        q = self
        r = self if n & 1 else Mod(1, self.n)

        i = 2
        while i <= n:
            q = (q * q)
            if n & i == i:
                r = (q * r)
            i = i << 1
        return r


@public
class Undefined(Mod):

    def __init__(self):
        object.__init__(self)

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
