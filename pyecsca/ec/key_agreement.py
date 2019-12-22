import hashlib
from typing import Optional, Any

from public import public

from .group import AbelianGroup
from .mult import ScalarMultiplier
from .point import Point


@public
class KeyAgreement(object):
    """An EC based key agreement primitive. (ECDH)"""
    mult: ScalarMultiplier
    group: AbelianGroup
    pubkey: Point
    privkey: int
    hash_algo: Optional[Any]

    def __init__(self, mult: ScalarMultiplier, group: AbelianGroup, pubkey: Point, privkey: int,
                 hash_algo: Optional[Any] = None):
        self.mult = mult
        self.group = group
        self.pubkey = pubkey
        self.privkey = privkey
        self.hash_algo = hash_algo
        self.mult.init(self.group, self.pubkey)

    def perform_raw(self) -> Point:
        """
        Perform the scalar-multiplication of the key agreement.

        :return: The shared point.
        """
        point = self.mult.multiply(self.privkey)
        return point.to_affine()  # TODO: This conversion should be somehow added to the context

    def perform(self) -> bytes:
        """
        Perform the key agreement operation.

        :return: The shared secret.
        """
        affine_point = self.perform_raw()
        x = int(affine_point.x)
        p = self.group.curve.prime
        n = (p.bit_length() + 7) // 8
        result = x.to_bytes(n, byteorder="big")
        if self.hash_algo is not None:
            result = self.hash_algo(result).digest()
        return result


@public
class ECDH_NONE(KeyAgreement):
    """Raw x-coordinate ECDH."""

    def __init__(self, mult: ScalarMultiplier, group: AbelianGroup, pubkey: Point, privkey: int):
        super().__init__(mult, group, pubkey, privkey)


@public
class ECDH_SHA1(KeyAgreement):
    """ECDH with SHA1 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, group: AbelianGroup, pubkey: Point, privkey: int):
        super().__init__(mult, group, pubkey, privkey, hashlib.sha1)


@public
class ECDH_SHA224(KeyAgreement):
    """ECDH with SHA224 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, group: AbelianGroup, pubkey: Point, privkey: int):
        super().__init__(mult, group, pubkey, privkey, hashlib.sha224)


@public
class ECDH_SHA256(KeyAgreement):
    """ECDH with SHA256 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, group: AbelianGroup, pubkey: Point, privkey: int):
        super().__init__(mult, group, pubkey, privkey, hashlib.sha256)


@public
class ECDH_SHA384(KeyAgreement):
    """ECDH with SHA384 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, group: AbelianGroup, pubkey: Point, privkey: int):
        super().__init__(mult, group, pubkey, privkey, hashlib.sha384)


@public
class ECDH_SHA512(KeyAgreement):
    """ECDH with SHA512 of x-coordinate."""

    def __init__(self, mult: ScalarMultiplier, group: AbelianGroup, pubkey: Point, privkey: int):
        super().__init__(mult, group, pubkey, privkey, hashlib.sha512)
