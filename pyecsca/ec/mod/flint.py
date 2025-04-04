import warnings
from functools import lru_cache, wraps, partial
from typing import Union

from public import public

from pyecsca.ec.error import (
    raise_non_invertible,
    raise_non_residue,
    NonResidueError,
    NonResidueWarning,
)
from pyecsca.ec.mod.base import Mod, cube_root_inner, square_root_inner

has_flint = False
try:
    import flint
    from flint.utils.flint_exceptions import DomainError

    _major, _minor, *_ = flint.__version__.split(".")
    if (int(_major), int(_minor)) >= (0, 5):
        has_flint = True
    else:
        flint = None
except ImportError:
    flint = None


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
    class FlintMod(Mod["FlintMod"]):
        """An element x of ℤₙ. Implemented by flint."""

        x: flint.fmpz_mod
        _ctx: flint.fmpz_mod_ctx
        __slots__ = ("x", "_ctx")

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
            except (ValueError, DomainError):
                raise_non_residue()

            if self.x == 0:
                return FlintMod(self._ctx(0), self._ctx, ensure=False)
            return square_root_inner(self, self._ctx, lambda x: FlintMod(x, self._ctx, ensure=False))

        def is_cubic_residue(self) -> bool:
            if not _fmpz_is_prime(self.n):
                raise NotImplementedError
            if self.x in (0, 1):
                return True
            if self.n % 3 == 2:
                return True
            pm1 = self.n - 1
            r = self ** (pm1 // 3)
            return r == 1

        def cube_root(self) -> "FlintMod":
            if not _fmpz_is_prime(self.n):
                raise NotImplementedError
            if self.x == 0:
                return FlintMod(self._ctx(0), self._ctx, ensure=False)
            if self.x == 1:
                return FlintMod(self._ctx(1), self._ctx, ensure=False)
            if not self.is_cubic_residue():
                raise_non_residue()
            return cube_root_inner(self, self._ctx, lambda x: FlintMod(x, self._ctx, ensure=False))

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

        def __pow__(self, n, _=None) -> "FlintMod":
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

    from pyecsca.ec.mod.base import _mod_classes

    _mod_classes["flint"] = FlintMod
