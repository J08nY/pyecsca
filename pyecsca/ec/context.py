from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from contextvars import ContextVar, Token
from copy import deepcopy
from typing import List, Optional, ContextManager, Any

from public import public


@public
class Action(object):
    """An Action."""
    inside: bool

    def __init__(self):
        self.inside = False

    def __enter__(self):
        getcontext().enter_action(self)
        self.inside = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        getcontext().exit_action(self)
        self.inside = False





class Tree(OrderedDict):

    def walk_get(self, path: List) -> Any:
        if len(path) == 0:
            return self
        value = self[path[0]]
        if isinstance(value, Tree):
            return value.walk_get(path[1:])
        elif len(path) == 1:
            return value
        else:
            raise ValueError


@public
class Context(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def enter_action(self, action: Action):
        ...

    @abstractmethod
    def exit_action(self, action: Action):
        ...

    def __str__(self):
        return self.__class__.__name__


@public
class NullContext(Context):
    """A context that does not trace any actions."""

    def enter_action(self, action: Action):
        pass

    def exit_action(self, action: Action):
        pass


@public
class DefaultContext(Context):
    """A context that traces executions of actions."""
    actions: Tree
    current: List[Action]

    def enter_action(self, action: Action):
        self.actions.walk_get(self.current)[action] = Tree()
        self.current.append(action)

    def exit_action(self, action: Action):
        if self.current[-1] != action:
            raise ValueError
        self.current.pop()

    def __init__(self):
        self.actions = Tree()
        self.current = []

    def __repr__(self):
        return f"{self.__class__.__name__}({self.actions}, current={self.current})"


_actual_context: ContextVar[Context] = ContextVar("operational_context", default=NullContext())


class _ContextManager(object):
    def __init__(self, new_context):
        self.new_context = deepcopy(new_context)

    def __enter__(self) -> Context:
        self.token = setcontext(self.new_context)
        return self.new_context

    def __exit__(self, t, v, tb):
        resetcontext(self.token)


@public
def getcontext() -> Context:
    """Get the current thread/task context."""
    return _actual_context.get()


@public
def setcontext(ctx: Context) -> Token:
    """
    Set the current thread/task context.

    :param ctx: A context to set.
    :return: A token to restore previous context.
    """
    return _actual_context.set(ctx)


@public
def resetcontext(token: Token):
    """
    Reset the context to a previous value.

    :param token: A token to restore.
    """
    _actual_context.reset(token)


@public
def local(ctx: Optional[Context] = None) -> ContextManager:
    """
    Use a local context.

    :param ctx: If none, current context is copied.
    :return: A context manager.
    """
    if ctx is None:
        ctx = getcontext()
    return _ContextManager(ctx)
