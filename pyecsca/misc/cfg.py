"""
Provides functions for runtime configuration of the toolkit.

This includes how errors are handled, or which :py:class:`~pyecsca.ec.mod.Mod` implementation is used.
"""
from copy import deepcopy
from contextvars import ContextVar, Token
from typing import Optional

from public import public


@public
class ECConfig:
    """Configuration for the :py:mod:`pyecsca.ec` package."""

    _no_inverse_action: str = "error"
    _non_residue_action: str = "error"
    _unsatisfied_formula_assumption_action: str = "error"
    _unsatisfied_coordinate_assumption_action: str = "error"
    _mod_implementation: str = "gmp"

    @property
    def no_inverse_action(self) -> str:
        """
        Return or set the action to take when a non-invertible element is to be inverted.

        One of:

         - ``"error"``: Raise :py:class:`pyecsca.ec.error.NonInvertibleError`.
         - ``"warning"``: Raise :py:class:`pyecsca.ec.error.NonInvertibleWarning`.
         - ``"ignore"``: Ignore the event and compute as if nothing happened.
        """
        return self._no_inverse_action

    @no_inverse_action.setter
    def no_inverse_action(self, value: str):
        if value not in ("error", "warning", "ignore"):
            raise ValueError("Action has to be one of 'error', 'warning', 'ignore'.")
        self._no_inverse_action = value

    @property
    def non_residue_action(self) -> str:
        """
        Return or set the action to take when a the square-root of a non-residue is to be computed.

        One of:

         - ``"error"``: Raise :py:class:`pyecsca.ec.error.NonResidueError`.
         - ``"warning"``: Raise :py:class:`pyecsca.ec.error.NonResidueWarning`.
         - ``"ignore"``: Ignore the event and compute as if nothing happened.
        """
        return self._non_residue_action

    @non_residue_action.setter
    def non_residue_action(self, value: str):
        if value not in ("error", "warning", "ignore"):
            raise ValueError("Action has to be one of 'error', 'warning', 'ignore'.")
        self._non_residue_action = value

    @property
    def unsatisfied_formula_assumption_action(self) -> str:
        """
        Return or set the action to take when a formula assumption is unsatisfied during execution.

        This works for assumption that can be ignored without a fatal error,
        which are those that are not used to compute a value of an undefined parameter.
        For example, things of the form ``Z1 = 1``.
        One of:

         - ``"error"``: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionError`.
         - ``"warning"``: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionWarning`.
         - ``"ignore"``: Ignore the event and compute as if nothing happened.
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
        Return or set the action to take when a coordinate assumption is unsatisfied during curve creation.

        This works for assumption that can be ignored without a fatal error,
        which are those that are not used to compute a value of an undefined parameter.
        For example, things of the form ``a = -1``.
        One of:

         - ``"error"``: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionError`.
         - ``"warning"``: Raise :py:class:`pyecsca.ec.error.UnsatisfiedAssumptionWarning`.
         - ``"ignore"``: Ignore the event and compute as if nothing happened.
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
        Return or set the selected :py:class:`pyecsca.ec.mod.Mod` implementation.

        One of:

         - ``"gmp"``: Requires the GMP library and `gmpy2` package.
         - ``"flint"``: Requires the flint library and `python-flint` package.
         - ``"python"``: Doesn't require anything.
         - ``"symbolic"``: Requires sympy.
        """
        return self._mod_implementation

    @mod_implementation.setter
    def mod_implementation(self, value: str):
        if value not in ("python", "gmp", "flint", "symbolic"):
            raise ValueError("Bad Mod implementaiton, can be one of 'python', 'gmp', 'flint' or 'symbolic'.")
        self._mod_implementation = value


@public
class LoggingConfig:
    """Logging configuration."""

    enabled: bool = True
    """Whether logging is enabled."""


@public
class Config:
    """Runtime configuration for the library."""

    ec: ECConfig
    """Configuration for the :py:mod:`pyecsca.ec` package."""
    log: LoggingConfig
    """Logging configuration."""

    def __init__(self):
        self.ec = ECConfig()
        self.log = LoggingConfig()


_config: ContextVar[Config] = ContextVar("config", default=Config())


@public
def getconfig() -> Config:
    """
    Get the current config.

    :return: The current config.
    """
    return _config.get()


@public
def setconfig(cfg: Config) -> Token:
    """
    Set the current config.

    :param cfg: The config to set.
    :return: A token that can be used to reset the config to the previous one.
    """
    return _config.set(cfg)


@public
def resetconfig(token: Token) -> None:
    """
    Reset the config to the previous one.

    :param token: A token from :py:func:`setconfig()`.
    """
    _config.reset(token)


@public
class TemporaryConfig:
    """
    Temporary config context manager.

    Can be entered as follows:

    .. code-block:: python

        with TemporaryConfig() as cfg:
            cfg.some_property = some_value
            ...
    """

    token: Optional[Token]

    def __init__(self):
        self.token = None
        self.new_config = deepcopy(getconfig())

    def __enter__(self) -> Config:
        self.token = setconfig(self.new_config)
        return self.new_config

    def __exit__(self, t, v, tb):
        if self.token:
            resetconfig(self.token)
