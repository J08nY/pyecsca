import hashlib
import secrets
from typing import Optional, Any

from asn1crypto.core import Sequence, SequenceOf, Integer
from public import public

from .context import getcontext
from .formula import AdditionFormula
from .mod import Mod
from .mult import ScalarMultiplier
from .point import Point


@public
class SignatureResult(object):
    """An ECDSA signature result (r, s)."""
    r: int
    s: int

    def __init__(self, r: int, s: int, data: Optional[bytes] = None, digest: Optional[bytes] = None,
                 nonce: Optional[int] = None, privkey: Optional[int] = None,
                 pubkey: Optional[Point] = None):
        self.r = r
        self.s = s

    @staticmethod
    def from_DER(data: bytes) -> "SignatureResult":
        """Load an ECDSA signature from ASN.1 DER data."""
        r, s = Sequence.load(data).native.values()
        return SignatureResult(r, s)

    def to_DER(self) -> bytes:
        """Output this signature into ASN.1 DER."""
        obj = SequenceOf(spec=Integer)
        obj.append(self.r)
        obj.append(self.s)
        return obj.dump()

    def __eq__(self, other):
        if not isinstance(other, SignatureResult):
            return False
        return self.r == other.r and self.s == other.s

    def __str__(self):
        return f"(r={self.r}, s={self.s})"

    def __repr__(self):
        return f"SignatureResult(r={self.r}, s={self.s})"


@public
class Signature(object):
    """An EC based signature primitive. (ECDSA)"""
    mult: ScalarMultiplier
    add: Optional[AdditionFormula]
    pubkey: Optional[Point]
    privkey: Optional[int]
    hash_algo: Optional[Any]

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[int] = None,
                 hash_algo: Optional[Any] = None):
        if pubkey is None and privkey is None:
            raise ValueError
        if add is None:
            if "add" not in mult.formulas:
                raise ValueError
            else:
                add = mult.formulas["add"]
        self.mult = mult
        self.add = add
        self.pubkey = pubkey
        self.privkey = privkey
        self.hash_algo = hash_algo

    @property
    def can_sign(self) -> bool:
        """Whether this instance can sign (has a private key)."""
        return self.privkey is not None

    @property
    def can_verify(self) -> bool:
        """Whether this instance can verify (has a public key and add formula)."""
        return self.pubkey is not None and self.add is not None

    def _get_nonce(self, nonce: Optional[int]) -> Mod:
        if nonce is None:
            return Mod(secrets.randbelow(self.mult.group.order), self.mult.group.order)
        else:
            return Mod(nonce, self.mult.group.order)

    def _do_sign(self, nonce: Mod, digest: bytes) -> SignatureResult:
        z = int.from_bytes(digest, byteorder="big")
        if len(digest) * 8 > self.mult.group.order.bit_length():
            z >>= len(digest) * 8 - self.mult.group.order.bit_length()
        point = self.mult.multiply(int(nonce), self.mult.group.generator)
        affine_point = point.to_affine()  #  TODO: add to context
        r = Mod(int(affine_point.x), self.mult.group.order)
        s = nonce.inverse() * (Mod(z, self.mult.group.order) + r * self.privkey)
        return SignatureResult(int(r), int(s), digest=digest, nonce=int(nonce),
                               privkey=self.privkey)

    def sign_hash(self, digest: bytes, nonce: Optional[int] = None) -> SignatureResult:
        """Sign already hashed data."""
        if not self.can_sign:
            raise RuntimeError("This instance cannot sign.")
        k = self._get_nonce(nonce)
        return self._do_sign(k, digest)

    def sign_data(self, data: bytes, nonce: Optional[int] = None) -> SignatureResult:
        """Sign data."""
        if not self.can_sign:
            raise RuntimeError("This instance cannot sign.")
        k = self._get_nonce(nonce)
        if self.hash_algo is None:
            digest = data
        else:
            digest = self.hash_algo(data).digest()
        return self._do_sign(k, digest)

    def _do_verify(self, signature: SignatureResult, digest: bytes) -> bool:
        z = int.from_bytes(digest, byteorder="big")
        if len(digest) * 8 > self.mult.group.order.bit_length():
            z >>= len(digest) * 8 - self.mult.group.order.bit_length()
        c = Mod(signature.s, self.mult.group.order).inverse()
        u1 = Mod(z, self.mult.group.order) * c
        u2 = Mod(signature.r, self.mult.group.order) * c
        p1 = self.mult.multiply(int(u1), self.mult.group.generator)
        p2 = self.mult.multiply(int(u2), self.pubkey)
        p = getcontext().execute(self.add, p1, p2, **self.mult.group.curve.parameters)[0]
        affine = p.to_affine()  # TODO: add to context
        v = Mod(int(affine.x), self.mult.group.order)
        return signature.r == int(v)

    def verify_hash(self, signature: SignatureResult, digest: bytes) -> bool:
        """Verify already hashed data."""
        if not self.can_verify:
            raise RuntimeError("This instance cannot verify.")
        return self._do_verify(signature, digest)

    def verify_data(self, signature: SignatureResult, data: bytes) -> bool:
        """Verify data."""
        if not self.can_verify:
            raise RuntimeError("This instance cannot verify.")
        if self.hash_algo is None:
            digest = data
        else:
            digest = self.hash_algo(data).digest()
        return self._do_verify(signature, digest)


@public
class ECDSA_NONE(Signature):
    """ECDSA with raw message input."""

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[int] = None):
        super().__init__(mult, add, pubkey, privkey)


@public
class ECDSA_SHA1(Signature):
    """ECDSA with SHA1."""

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[int] = None):
        super().__init__(mult, add, pubkey, privkey, hashlib.sha1)


@public
class ECDSA_SHA224(Signature):
    """ECDSA with SHA224."""

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[int] = None):
        super().__init__(mult, add, pubkey, privkey, hashlib.sha224)


@public
class ECDSA_SHA256(Signature):
    """ECDSA with SHA256."""

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[int] = None):
        super().__init__(mult, add, pubkey, privkey, hashlib.sha256)


@public
class ECDSA_SHA384(Signature):
    """ECDSA with SHA384."""

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[int] = None):
        super().__init__(mult, add, pubkey, privkey, hashlib.sha384)


@public
class ECDSA_SHA512(Signature):
    """ECDSA with SHA512."""

    def __init__(self, mult: ScalarMultiplier, add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[int] = None):
        super().__init__(mult, add, pubkey, privkey, hashlib.sha512)
