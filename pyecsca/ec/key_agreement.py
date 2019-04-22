import hashlib
from typing import Optional, Any

from public import public

from .mult import ScalarMultiplier
from .point import Point


@public
class KeyAgreement(object):
    mult: ScalarMultiplier
    pubkey: Point
    privkey: int
    hash_algo: Optional[Any]

    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int,
                 hash_algo: Optional[Any] = None):
        self.mult = mult
        self.pubkey = pubkey
        self.privkey = privkey
        self.hash_algo = hash_algo

    def perform(self):
        point = self.mult.multiply(self.privkey, self.pubkey)
        affine_point = point.to_affine()  # TODO: This conversion should be somehow added to the context
        x = int(affine_point.x)
        p = self.mult.group.curve.prime
        n = (p.bit_length() + 7) // 8
        result = x.to_bytes(n, byteorder="big")
        if self.hash_algo is not None:
            result = self.hash_algo(result).digest()
        return result


@public
class ECDH_NONE(KeyAgreement):
    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        super().__init__(mult, pubkey, privkey)


@public
class ECDH_SHA1(KeyAgreement):
    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        super().__init__(mult, pubkey, privkey, hashlib.sha1)


@public
class ECDH_SHA224(KeyAgreement):
    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        super().__init__(mult, pubkey, privkey, hashlib.sha224)


@public
class ECDH_SHA256(KeyAgreement):
    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        super().__init__(mult, pubkey, privkey, hashlib.sha256)


@public
class ECDH_SHA384(KeyAgreement):
    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        super().__init__(mult, pubkey, privkey, hashlib.sha384)


@public
class ECDH_SHA512(KeyAgreement):
    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        super().__init__(mult, pubkey, privkey, hashlib.sha512)
