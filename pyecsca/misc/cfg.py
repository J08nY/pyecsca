from copy import deepcopy
from contextvars import ContextVar, Token

from public import public


@public
class ECConfig(object):
    """Configuration for the :py:mod:`pyecsca.ec` package."""
    _no_inverse_action: str = "error"
    _non_residue_action: str = "error"
    _unsatisfied_formula_assumption_action: str = "error"
    _unsatisfied_coordinate_assumption_action: str = "error"
    _mod_implementation: str = "gmp"

    @property
    def no_inverse_action(self) -> str:
        """
        The action to take when a non-invertible element is to be inverted. One of:

         - `"error"`: Raise :py:class:`pyecsca.ec.error.NonInvertibleError`.
         - `"warning"`: Raise :py:class:`pyecsca.ec.error.NonInvertibleWarning`.
         - `"ignore"`: Ignore the event and compute as if nothing happened."""
        return self._no_inverse_action

    @no_inverse_action.setter
    def no_inverse_action(self, value: str):
        if value not in ("error", "warning", "ignore"):
            raise ValueError("Action has to be one of 'error', 'warning', 'ignore'.")
        self._no_inverse_action = value

    @property
    def non_residue_action(self) -> str:
        """
        The action to take when a the square-root of a non-residue is to be computed. One of:

         - `"error"`: Raise :py:class:`pyecsca.ec.error.NonResidueError`.
         - `"warning"`: Raise :py:class:`pyecsca.ec.error.NonResidueWarning`.
         - `"ignore"`: Ignore the event and compute as if nothing happened."""
        return self._non_residue_action

    @non_residue_action.setter
    def non_residue_action(self, value: str):
        if value not in ("error", "warning", "ignore"):
            raise ValueError("Action has to be one of 'error', 'warning', 'ignore'.")
        self._non_residue_action = value

    @property
    def unsatisfied_formula_assumption_action(self) -> str:
        """
        The action to take when a formula assumption is unsatisfied during execution.
        This works for assumption that can be ignored without a fatal error,
        which are those that are not used to compute a value of an undefined parameter.
        For example, things of the form `Z1 = 1`.
        One of:

         - `"error"`: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionError`.
         - `"warning"`: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionWarning`.
         - `"ignore"`: Ignore the event and compute as if nothing happened.
        """
        return self._unsatisfied_formula_assumption_action

    @unsatisfied_formula_assumption_action.setter
    def unsatisfied_formula_assumption_action(self, value: str):
        if value not in ("error", "warning", "ignore"):
            raise ValueError("Action has to be one of 'error', 'warning', 'ignore'.")
        self._unsatisfied_formula_assumption_action = value

    @property
    def unsatisfied_coordinate_assumption_action(self) -> str:
        """
        The action to take when a coordinate assumption is unsatisfied during curve creation.
        This works for assumption that can be ignored without a fatal error,
        which are those that are not used to compute a value of an undefined parameter.
        For example, things of the form `a = -1`.
        One of:

         - `"error"`: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionError`.
         - `"warning"`: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionWarning`.
         - `"ignore"`: Ignore the event and compute as if nothing happened.
        """
        return self._unsatisfied_coordinate_assumption_action

    @unsatisfied_coordinate_assumption_action.setter
    def unsatisfied_coordinate_assumption_action(self, value: str):
        if value not in ("error", "warning", "ignore"):
            raise ValueError("Action has to be one of 'error', 'warning', 'ignore'.")
        self._unsatisfied_coordinate_assumption_action = value

    @property
    def mod_implementation(self) -> str:
        """
        The selected :py:class:`pyecsca.ec.mod.Mod` implementation. One of:

         - `"gmp"`: Requires the GMP library and `gmpy2` package.
         - `"python"`: Doesn't require anything.
        """
        return self._mod_implementation

    @mod_implementation.setter
    def mod_implementation(self, value: str):
        if value not in ("python", "gmp"):
            raise ValueError("Bad Mod implementaiton, can be one of 'python' or 'gmp'.")
        self._mod_implementation = value


@public
class Config(object):
    """A runtime configuration for the library."""
    ec: ECConfig
    """Configuration for the :py:mod:`pyecsca.ec` package."""

    def __init__(self):
        self.ec = ECConfig()


_config: ContextVar[Config] = ContextVar("config", default=Config())


@public
def getconfig() -> Config:
    return _config.get()


@public
def setconfig(cfg: Config) -> Token:
    return _config.set(cfg)


@public
def resetconfig(token: Token):
    _config.reset(token)


@public
class TemporaryConfig(object):
    def __init__(self):
        self.new_config = deepcopy(getconfig())

    def __enter__(self) -> Config:
        self.token = setconfig(self.new_config)
        return self.new_config

    def __exit__(self, t, v, tb):
        resetconfig(self.token)
