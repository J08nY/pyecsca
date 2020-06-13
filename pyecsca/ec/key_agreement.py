import hashlib
from typing import Optional, Any

from public import public

from .context import ResultAction
from .mod import Mod
from .mult import ScalarMultiplier
from .params import DomainParameters
from .point import Point


@public
class ECDHAction(ResultAction):
    """An ECDH key exchange."""
    params: DomainParameters
    hash_algo: Optional[Any]
    privkey: Mod
    pubkey: Point

    def __init__(self, params: DomainParameters, hash_algo: Optional[Any],
                 privkey: Mod,
                 pubkey: Point):
        super().__init__()
        self.params = params
        self.hash_algo = hash_algo
        self.privkey = privkey
        self.pubkey = pubkey

    def __repr__(self):
        return f"{self.__class__.__name__}({self.params}, {self.hash_algo}, {self.privkey}, {self.pubkey})"


@public
class KeyAgreement(object):
    """An EC based key agreement primitive. (ECDH)"""
    mult: ScalarMultiplier
    params: DomainParameters
    pubkey: Point
    privkey: Mod
    hash_algo: Optional[Any]

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, pubkey: Point, privkey: Mod,
                 hash_algo: Optional[Any] = None):
        self.mult = mult
        self.params = params
        self.pubkey = pubkey
        self.privkey = privkey
        self.hash_algo = hash_algo
        self.mult.init(self.params, self.pubkey)

    def perform_raw(self) -> Point:
        """
        Perform the scalar-multiplication of the key agreement.

        :return: The shared point.
        """
        point = self.mult.multiply(int(self.privkey))
        return point.to_affine()

    def perform(self) -> bytes:
        """
        Perform the key agreement operation.

        :return: The shared secret.
        """
        with ECDHAction(self.params, self.hash_algo, self.privkey, self.pubkey) as action:
            affine_point = self.perform_raw()
            x = int(affine_point.x)
            p = self.params.curve.prime
            n = (p.bit_length() + 7) // 8
            result = x.to_bytes(n, byteorder="big")
            if self.hash_algo is not None:
                result = self.hash_algo(result).digest()
            return action.exit(result)


@public
class ECDH_NONE(KeyAgreement):
    """Raw x-coordinate ECDH."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, pubkey: Point,
                 privkey: Mod):
        super().__init__(mult, params, pubkey, privkey)


@public
class ECDH_SHA1(KeyAgreement):
    """ECDH with SHA1 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, pubkey: Point,
                 privkey: Mod):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha1)


@public
class ECDH_SHA224(KeyAgreement):
    """ECDH with SHA224 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, pubkey: Point,
                 privkey: Mod):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha224)


@public
class ECDH_SHA256(KeyAgreement):
    """ECDH with SHA256 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, pubkey: Point,
                 privkey: Mod):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha256)


@public
class ECDH_SHA384(KeyAgreement):
    """ECDH with SHA384 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, pubkey: Point,
                 privkey: Mod):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha384)


@public
class ECDH_SHA512(KeyAgreement):
    """ECDH with SHA512 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, pubkey: Point,
                 privkey: Mod):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha512)
