from public import public
from ..misc.cfg import getconfig


@public
class NonInvertibleError(ArithmeticError):
    pass


@public
class NonInvertibleWarning(UserWarning):
    pass


def raise_non_invertible():
    """Raise either :py:class:`NonInvertibleError` or :py:class:`NonInvertiblerWarning` or ignore.
    Depends on the current config value of `no_inverse_action`."""
    cfg = getconfig()
    if cfg.ec.no_inverse_action == "error":
        raise NonInvertibleError("Element not invertible.")
    elif cfg.ec.no_inverse_action == "warning":
        raise NonInvertibleWarning("Element not invertible.")


@public
class NonResidueError(ArithmeticError):
    pass


@public
class NonResidueWarning(UserWarning):
    pass


def raise_non_residue():
    """Raise either :py:class:`NonResidueError` or :py:class:`NonResidueWarning` or ignore.
    Depends on the current config value of `non_residue_action`."""
    cfg = getconfig()
    if cfg.ec.non_residue_action == "error":
        raise NonResidueError("No square root exists.")
    elif cfg.ec.non_residue_action == "warning":
        raise NonResidueWarning("No square root exists.")


@public
class UnsatisfiedAssumptionError(ValueError):
    pass


@public
class UnsatisfiedAssumptionWarning(UserWarning):
    pass


def raise_unsatisified_assumption(action: str, msg: str):
    """Raise either :py:class:`UnsatisfiedAssumptionError` or :py:class:`UnsatisfiedAssumptionWarning` or ignore.
    Depends on the value of `action`."""
    if action == "error":
        raise UnsatisfiedAssumptionError(msg)
    elif action == "warning":
        raise UnsatisfiedAssumptionWarning(msg)
