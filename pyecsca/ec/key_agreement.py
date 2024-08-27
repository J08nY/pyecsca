"""Provides an implementation of ECDH (Elliptic Curve Diffie-Hellman) and XDH (X25519, X448)."""

import hashlib
from abc import abstractmethod, ABC
from typing import Optional, Any

from public import public

from pyecsca.ec.context import ResultAction
from pyecsca.ec.mod import Mod
from pyecsca.ec.model import MontgomeryModel
from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.params import DomainParameters, get_params
from pyecsca.ec.point import Point


@public
class ECDHAction(ResultAction):
    """ECDH key exchange."""

    params: DomainParameters
    hash_algo: Optional[Any]
    privkey: Mod
    pubkey: Point

    def __init__(
        self,
        params: DomainParameters,
        hash_algo: Optional[Any],
        privkey: Mod,
        pubkey: Point,
    ):
        super().__init__()
        self.params = params
        self.hash_algo = hash_algo
        self.privkey = privkey
        self.pubkey = pubkey

    def __repr__(self):
        return f"{self.__class__.__name__}({self.params}, {self.hash_algo}, {self.privkey}, {self.pubkey})"


@public
class XDHAction(ResultAction):
    """XDH key exchange."""

    params: DomainParameters
    privkey: int
    pubkey: Point

    def __init__(self, params: DomainParameters, privkey: int, pubkey: Point):
        super().__init__()
        self.params = params
        self.privkey = privkey
        self.pubkey = pubkey

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.params}, {self.privkey}, {self.pubkey})"
        )


@public
class KeyAgreement(ABC):
    """An abstract EC-based key agreement."""

    @abstractmethod
    def perform_raw(self) -> Point:
        """
        Perform the scalar-multiplication of the key agreement.

        :return: The shared point.
        """
        ...

    @abstractmethod
    def perform(self) -> bytes:
        """
        Perform the key agreement operation.

        :return: The shared secret.
        """
        ...


@public
class XDH(KeyAgreement):
    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: int,
        bits: int,
        bytes: int,
    ):
        if "scl" not in mult.formulas:
            raise ValueError("ScalarMultiplier needs to have the scaling formula.")
        if not isinstance(params.curve.model, MontgomeryModel):
            raise ValueError("Invalid curve model.")
        self.mult = mult
        self.params = params
        self.pubkey = pubkey
        self.privkey = privkey
        self.bits = bits
        self.bytes = bytes
        self.mult.init(self.params, self.pubkey)

    def clamp(self, scalar: int) -> int:
        return scalar

    def perform_raw(self) -> Point:
        clamped = self.clamp(self.privkey)
        return self.mult.multiply(clamped)

    def perform(self) -> bytes:
        with XDHAction(self.params, self.privkey, self.pubkey) as action:
            point = self.perform_raw()
            return action.exit(int(point.X).to_bytes(self.bytes, "little"))


@public
class X25519(XDH):
    """
    X25519 (or Curve25519) from [RFC7748]_.

    .. warning::
        You need to clear the top bit of the point coordinate (pubkey) before converting to a point.
    """

    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        curve25519 = get_params(
            "other", "Curve25519", pubkey.coordinate_model.name, infty=False
        )
        super().__init__(mult, curve25519, pubkey, privkey, 255, 32)

    def clamp(self, scalar: int) -> int:
        scalar &= ~7
        scalar &= ~(128 << 8 * 31)
        scalar |= 64 << 8 * 31
        return scalar


@public
class X448(XDH):
    """
    X448 (or Curve448) from [RFC7748]_.
    """

    def __init__(self, mult: ScalarMultiplier, pubkey: Point, privkey: int):
        curve448 = get_params(
            "other", "Curve448", pubkey.coordinate_model.name, infty=False
        )
        super().__init__(mult, curve448, pubkey, privkey, 448, 56)

    def clamp(self, scalar: int) -> int:
        scalar &= ~3
        scalar |= 128 << 8 * 55
        return scalar


@public
class ECDH(KeyAgreement):
    """EC based key agreement primitive (ECDH)."""

    mult: ScalarMultiplier
    params: DomainParameters
    pubkey: Point
    privkey: Mod
    hash_algo: Optional[Any]

    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: Mod,
        hash_algo: Optional[Any] = None,
    ):
        self.mult = mult
        self.params = params
        self.pubkey = pubkey
        self.privkey = privkey
        self.hash_algo = hash_algo
        self.mult.init(self.params, self.pubkey)

    def perform_raw(self) -> Point:
        point = self.mult.multiply(int(self.privkey))
        return point.to_affine()

    def perform(self) -> bytes:
        with ECDHAction(
            self.params, self.hash_algo, self.privkey, self.pubkey
        ) as action:
            affine_point = self.perform_raw()
            x = int(affine_point.x)
            p = self.params.curve.prime
            n = (p.bit_length() + 7) // 8
            result = x.to_bytes(n, byteorder="big")
            if self.hash_algo is not None:
                result = self.hash_algo(result).digest()
            return action.exit(result)


@public
class ECDH_NONE(ECDH):
    """Raw x-coordinate ECDH."""

    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: Mod,
    ):
        super().__init__(mult, params, pubkey, privkey)


@public
class ECDH_SHA1(ECDH):
    """ECDH with SHA1 of x-coordinate."""

    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: Mod,
    ):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha1)


@public
class ECDH_SHA224(ECDH):
    """ECDH with SHA224 of x-coordinate."""

    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: Mod,
    ):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha224)


@public
class ECDH_SHA256(ECDH):
    """ECDH with SHA256 of x-coordinate."""

    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: Mod,
    ):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha256)


@public
class ECDH_SHA384(ECDH):
    """ECDH with SHA384 of x-coordinate."""

    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: Mod,
    ):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha384)


@public
class ECDH_SHA512(ECDH):
    """ECDH with SHA512 of x-coordinate."""

    def __init__(
        self,
        mult: ScalarMultiplier,
        params: DomainParameters,
        pubkey: Point,
        privkey: Mod,
    ):
        super().__init__(mult, params, pubkey, privkey, hashlib.sha512)
