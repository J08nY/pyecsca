from typing import Tuple

from public import public

from .context import ResultAction
from .mod import Mod
from .mult import ScalarMultiplier
from .params import DomainParameters
from .point import Point


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
class KeyGeneration(object):
    """Key generator."""
    mult: ScalarMultiplier
    params: DomainParameters
    affine: bool

    def __init__(self, mult: ScalarMultiplier, params: DomainParameters, affine: bool = False):
        self.mult = mult
        self.params = params
        self.mult.init(self.params, self.params.generator)
        self.affine = affine

    def generate(self) -> Tuple[Mod, Point]:
        with KeygenAction(self.params) as action:
            privkey = Mod.random(self.params.order)
            pubkey = self.mult.multiply(privkey.x)
            if self.affine:
                pubkey = pubkey.to_affine()
            return action.exit((privkey, pubkey))
