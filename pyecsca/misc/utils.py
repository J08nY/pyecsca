"""Just some utilities I promise."""
import sys
from ast import parse
from contextlib import contextmanager
from typing import List, Any, Generator

from ..misc.cfg import getconfig, TemporaryConfig

from concurrent.futures import ProcessPoolExecutor, as_completed, Future


def pexec(s):
    return parse(s, mode="exec")


def peval(s):
    return parse(s, mode="eval")


def in_notebook() -> bool:
    """Test whether we are executing in Jupyter notebook."""
    try:
        from IPython import get_ipython

        if "IPKernelApp" not in get_ipython().config:  # pragma: no cover
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


@contextmanager
def silent():
    """Temporarily disable output."""
    with TemporaryConfig() as cfg:
        cfg.log.enabled = False
        yield


class TaskExecutor(ProcessPoolExecutor):
    """A simple ProcessPoolExecutor that keeps tracks of tasks that were submitted to it."""

    keys: List[Any]
    futures: List[Future]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = []
        self.futures = []

    def submit_task(self, key: Any, fn, /, *args, **kwargs):
        future = self.submit(fn, *args, **kwargs)
        self.futures.append(future)
        self.keys.append(key)
        return future

    @property
    def tasks(self):
        return list(zip(self.keys, self.futures))

    def as_completed(self) -> Generator[tuple[Any, Future], Any, None]:
        for future in as_completed(self.futures):
            i = self.futures.index(future)
            yield self.keys[i], future
        self.futures = []
        self.keys = []
