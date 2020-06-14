import hashlib
import secrets
from typing import Optional, Any

from asn1crypto.core import Sequence, SequenceOf, Integer
from public import public

from .context import Action
from .formula import AdditionFormula
from .mod import Mod
from .mult import ScalarMultiplier
from .params import DomainParameters
from .point import Point


@public
class SignatureResult(object):
    """An ECDSA signature result (r, s)."""
    r: int
    s: int

    def __init__(self, r: int, s: int, data: Optional[bytes] = None, digest: Optional[bytes] = None,
                 nonce: Optional[int] = None, privkey: Optional[Mod] = None,
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
class ECDSAAction(Action):
    """An ECDSA action base class."""
    params: DomainParameters
    hash_algo: Optional[Any]
    msg: bytes

    def __init__(self, params: DomainParameters, hash_algo: Optional[Any],
                 msg: bytes):
        super().__init__()
        self.params = params
        self.hash_algo = hash_algo
        self.msg = msg

    def __repr__(self):
        return f"{self.__class__.__name__}({self.params}, {self.hash_algo}, {self.msg})"


@public
class ECDSASignAction(ECDSAAction):
    """An ECDSA signing."""
    privkey: Mod

    def __init__(self, params: DomainParameters, hash_algo: Optional[Any], msg: bytes,
                 privkey: Mod):
        super().__init__(params, hash_algo, msg)
        self.privkey = privkey

    def __repr__(self):
        return f"{self.__class__.__name__}({self.params}, {self.hash_algo}, {self.msg}, {self.privkey})"


@public
class ECDSAVerifyAction(ECDSAAction):
    """An ECDSA verification."""
    signature: SignatureResult
    pubkey: Point

    def __init__(self, params: DomainParameters, hash_algo: Optional[Any], msg: bytes,
                 signature: SignatureResult, pubkey: Point):
        super().__init__(params, hash_algo, msg)
        self.signature = signature
        self.pubkey = pubkey

    def __repr__(self):
        return f"{self.__class__.__name__}({self.params}, {self.hash_algo}, {self.msg}, {self.signature}, {self.pubkey})"


@public
class Signature(object):
    """An EC based signature primitive. (ECDSA)"""
    mult: ScalarMultiplier
    params: DomainParameters
    add: Optional[AdditionFormula]
    pubkey: Optional[Point]
    privkey: Optional[Mod]
    hash_algo: Optional[Any]

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters,
                 add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[Mod] = None,
                 hash_algo: Optional[Any] = None):
        if pubkey is None and privkey is None:
            raise ValueError
        if add is None:
            if "add" not in mult.formulas:
                raise ValueError
            elif isinstance(mult.formulas["add"], AdditionFormula):
                add = mult.formulas["add"]
        self.mult = mult
        self.params = params
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
            return Mod.random(self.params.order)
        else:
            return Mod(nonce, self.params.order)

    def _do_sign(self, nonce: Mod, digest: bytes) -> SignatureResult:
        z = int.from_bytes(digest, byteorder="big")
        if len(digest) * 8 > self.params.order.bit_length():
            z >>= len(digest) * 8 - self.params.order.bit_length()
        self.mult.init(self.params, self.params.generator)
        point = self.mult.multiply(int(nonce))
        affine_point = point.to_affine()
        r = Mod(int(affine_point.x), self.params.order)
        s = nonce.inverse() * (Mod(z, self.params.order) + r * self.privkey)
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
        if not self.can_sign or self.privkey is None:
            raise RuntimeError("This instance cannot sign.")
        with ECDSASignAction(self.params, self.hash_algo, data, self.privkey):
            k = self._get_nonce(nonce)
            if self.hash_algo is None:
                digest = data
            else:
                digest = self.hash_algo(data).digest()
            return self._do_sign(k, digest)

    def _do_verify(self, signature: SignatureResult, digest: bytes) -> bool:
        if self.pubkey is None or self.add is None:
            return False
        z = int.from_bytes(digest, byteorder="big")
        if len(digest) * 8 > self.params.order.bit_length():
            z >>= len(digest) * 8 - self.params.order.bit_length()
        c = Mod(signature.s, self.params.order).inverse()
        u1 = Mod(z, self.params.order) * c
        u2 = Mod(signature.r, self.params.order) * c
        self.mult.init(self.params, self.params.generator)
        p1 = self.mult.multiply(int(u1))
        self.mult.init(self.params, self.pubkey)
        p2 = self.mult.multiply(int(u2))
        p = self.add(p1, p2, **self.params.curve.parameters)[0]
        affine = p.to_affine()
        v = Mod(int(affine.x), self.params.order)
        return signature.r == int(v)

    def verify_hash(self, signature: SignatureResult, digest: bytes) -> bool:
        """Verify already hashed data."""
        if not self.can_verify:
            raise RuntimeError("This instance cannot verify.")
        return self._do_verify(signature, digest)

    def verify_data(self, signature: SignatureResult, data: bytes) -> bool:
        """Verify data."""
        if not self.can_verify or self.pubkey is None:
            raise RuntimeError("This instance cannot verify.")
        with ECDSAVerifyAction(self.params, self.hash_algo, data, signature, self.pubkey):
            if self.hash_algo is None:
                digest = data
            else:
                digest = self.hash_algo(data).digest()
            return self._do_verify(signature, digest)


@public
class ECDSA_NONE(Signature):
    """ECDSA with raw message input."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters,
                 add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[Mod] = None):
        super().__init__(mult, params, add, pubkey, privkey)


@public
class ECDSA_SHA1(Signature):
    """ECDSA with SHA1."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters,
                 add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[Mod] = None):
        super().__init__(mult, params, add, pubkey, privkey, hashlib.sha1)


@public
class ECDSA_SHA224(Signature):
    """ECDSA with SHA224."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters,
                 add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[Mod] = None):
        super().__init__(mult, params, add, pubkey, privkey, hashlib.sha224)


@public
class ECDSA_SHA256(Signature):
    """ECDSA with SHA256."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters,
                 add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[Mod] = None):
        super().__init__(mult, params, add, pubkey, privkey, hashlib.sha256)


@public
class ECDSA_SHA384(Signature):
    """ECDSA with SHA384."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters,
                 add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[Mod] = None):
        super().__init__(mult, params, add, pubkey, privkey, hashlib.sha384)


@public
class ECDSA_SHA512(Signature):
    """ECDSA with SHA512."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters,
                 add: Optional[AdditionFormula] = None,
                 pubkey: Optional[Point] = None, privkey: Optional[Mod] = None):
        super().__init__(mult, params, add, pubkey, privkey, hashlib.sha512)
