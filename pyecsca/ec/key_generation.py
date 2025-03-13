"""Provides a key generator for elliptic curve keypairs."""

from typing import Tuple

from public import public

from pyecsca.ec.context import ResultAction
from pyecsca.ec.mod import Mod
from pyecsca.ec.mult import ScalarMultiplier
from pyecsca.ec.params import DomainParameters
from pyecsca.ec.point import Point


@public
class KeygenAction(ResultAction):
    """A key generation."""

    params: DomainParameters

    def __init__(self, params: DomainParameters):
        super().__init__()
        self.params = params

    def __repr__(self):
        return f"{self.__class__.__name__}({self.params})"


@public
class KeyGeneration:
    """
    Key generator.

    :param mult: The scalar multiplier to use during key generation.
    :param params: The domain parameters over which to generate the keypair.
    :param affine: Whether to transform the public key point to the affine form during key generation.
    """

    mult: ScalarMultiplier
    params: DomainParameters
    affine: bool

    def __init__(
        self, mult: ScalarMultiplier, params: DomainParameters, affine: bool = False
    ):
        self.mult = mult
        self.params = params
        self.mult.init(self.params, self.params.generator)
        self.affine = affine

    def generate(self) -> Tuple[Mod, Point]:
        """
        Generate a keypair.

        :return: The generated keypair, a `tuple` of the private key (scalar) and the public key (point).
        """
        with KeygenAction(self.params) as action:
            privkey = Mod.random(self.params.order)
            pubkey = self.mult.multiply(int(privkey.x))
            if self.affine:
                pubkey = pubkey.to_affine()
            return action.exit((privkey, pubkey))
