"""Contains exceptions and warnings used in the library."""
import warnings
from public import public
from pyecsca.misc.cfg import getconfig


@public
class NonInvertibleError(ArithmeticError):
    """Non-invertible element was inverted."""

    pass


@public
class NonInvertibleWarning(UserWarning):
    """Non-invertible element was inverted."""

    pass


def raise_non_invertible():
    """
    Raise either :py:class:`NonInvertibleError` or :py:class:`NonInvertiblerWarning` or ignore.

    Depends on the current config value of :py:attr:`Config.ec.no_inverse_action`.
    """
    cfg = getconfig()
    if cfg.ec.no_inverse_action == "error":
        raise NonInvertibleError("Element not invertible.")
    elif cfg.ec.no_inverse_action == "warning":
        warnings.warn(NonInvertibleWarning("Element not invertible."))


@public
class NonResidueError(ArithmeticError):
    """Non-residue element was square-rooted."""

    pass


@public
class NonResidueWarning(UserWarning):
    """Non-residue element was square-rooted."""

    pass


def raise_non_residue():
    """
    Raise either :py:class:`NonResidueError` or :py:class:`NonResidueWarning` or ignore.

    Depends on the current config value of :py:attr:`Config.ec.non_residue_action`.
    """
    cfg = getconfig()
    if cfg.ec.non_residue_action == "error":
        raise NonResidueError("No square root exists.")
    elif cfg.ec.non_residue_action == "warning":
        warnings.warn(NonResidueWarning("No square root exists."))


@public
class UnsatisfiedAssumptionError(ValueError):
    """Unsatisfied assumption was hit."""

    pass


@public
class UnsatisfiedAssumptionWarning(UserWarning):
    """Unsatisfied assumption was hit."""

    pass


def raise_unsatisified_assumption(action: str, msg: str):
    """
    Raise either :py:class:`UnsatisfiedAssumptionError` or :py:class:`UnsatisfiedAssumptionWarning` or ignore.

    Depends on the value of :paramref:`~.raise_unsatisified_assumption.action`.
    """
    if action == "error":
        raise UnsatisfiedAssumptionError(msg)
    elif action == "warning":
        warnings.warn(UnsatisfiedAssumptionWarning(msg))
