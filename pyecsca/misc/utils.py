"""Just some utilities I promise."""
import sys
from ast import parse

from pyecsca.misc.cfg import getconfig


def pexec(s):
    return parse(s, mode="exec")


def peval(s):
    return parse(s, mode="eval")


def in_notebook() -> bool:
    """Test whether we are executing in Jupyter notebook."""
    try:
        from IPython import get_ipython
        if 'IPKernelApp' not in get_ipython().config:  # pragma: no cover
            return False
    except ImportError:
        return False
    except AttributeError:
        return False
    return True


def log(*args, **kwargs):
    """Log a message."""
    if in_notebook() and getconfig().log.enabled:
        print(*args, **kwargs)


def warn(*args, **kwargs):
    """Log a message."""
    if in_notebook() and getconfig().log.enabled:
        print(*args, **kwargs, file=sys.stderr)
