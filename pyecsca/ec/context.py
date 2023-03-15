"""
Provides classes for tracing the execution of operations.

The operations include key generation, scalar multiplication, formula execution and individual operation evaluation.
These operations are traced in `Context` classes using `Actions`. Different contexts trace actions differently.

A :py:class:`DefaultContext` traces actions into a tree as they are executed (a scalar
multiplication actions has as its children an ordered list of the individual formula executions it has done).

A :py:class:`PathContext` works like a :py:class:`DefaultContext` that only traces an action on a particular path
in the tree.

A :py:class:`NullContext` does not trace any actions and is the default context.
"""
from abc import abstractmethod, ABC
from collections import OrderedDict
from copy import deepcopy
from typing import List, Optional, ContextManager, Any, Tuple, Sequence

from public import public


@public
class Action:
    """An Action."""

    inside: bool

    def __init__(self):
        self.inside = False

    def __enter__(self):
        if current is not None:
            current.enter_action(self)
        self.inside = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if current is not None:
            current.exit_action(self)
        self.inside = False


@public
class ResultAction(Action):
    """An action that has a result."""

    _result: Any = None
    _has_result: bool = False

    @property
    def result(self) -> Any:
        if not self._has_result:
            raise AttributeError("No result set")
        return self._result

    def exit(self, result: Any):
        if not self.inside:
            raise RuntimeError("Result set outside of action scope")
        if self._has_result:
            return
        self._has_result = True
        self._result = result
        return result

    def __exit__(self, exc_type, exc_val, exc_tb):
        if (
                not self._has_result
                and exc_type is None
                and exc_val is None
                and exc_tb is None
        ):
            raise RuntimeError("Result unset on action exit")
        super().__exit__(exc_type, exc_val, exc_tb)


@public
class Tree(OrderedDict):
    """A recursively-implemented tree."""

    def get_by_key(self, path: List) -> Any:
        """
        Get the value in the tree at a position given by the path.

        :param path: The path to get.
        :return: The value in the tree.
        """
        if len(path) == 0:
            return self
        value = self[path[0]]
        if len(path) == 1:
            return value
        elif isinstance(value, Tree):
            return value.get_by_key(path[1:])
        else:
            raise ValueError

    def get_by_index(self, path: List[int]) -> Tuple[Any, Any]:
        """
        Get the key and value in the tree at a position given by the path of indices.

        The nodes inside a level of a tree are ordered by insertion order.

        :param path: The path to get.
        :return: The key and value.
        """
        if len(path) == 0:
            raise ValueError
        key = list(self.keys())[path[0]]
        value = self[key]
        if len(path) == 1:
            return key, value
        elif isinstance(value, Tree):
            return value.get_by_index(path[1:])
        else:
            raise ValueError

    def repr(self, depth: int = 0) -> str:
        """
        Construct a textual representation of the tree. Useful for visualization and debugging.

        :param depth:
        :return: The resulting textual representation.
        """
        result = ""
        for key, value in self.items():
            if isinstance(value, Tree):
                result += "\t" * depth + str(key) + "\n"
                result += value.repr(depth + 1)
            else:
                result += "\t" * depth + str(key) + ":" + str(value) + "\n"
        return result

    def __repr__(self):
        return self.repr()


@public
class Context(ABC):
    """
    Context is an object that traces actions which happen.

    There is always one context active, see functions :py:func:`getcontext`,
    :py:func:`setcontext` and :py:func:`resetcontext`.
    """

    @abstractmethod
    def enter_action(self, action: Action) -> None:
        """
        Enter into an action (i.e. start executing it).

        :param action: The action.
        """
        raise NotImplementedError

    @abstractmethod
    def exit_action(self, action: Action) -> None:
        """
        Exit from an action (i.e. stop executing it).

        :param action: The action.
        """
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__


@public
class DefaultContext(Context):
    """Context that traces executions of actions in a tree."""

    actions: Tree
    current: List[Action]

    def __init__(self):
        self.actions = Tree()
        self.current = []

    def enter_action(self, action: Action) -> None:
        self.actions.get_by_key(self.current)[action] = Tree()
        self.current.append(action)

    def exit_action(self, action: Action) -> None:
        if len(self.current) < 1 or self.current[-1] != action:
            raise ValueError
        self.current.pop()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.actions!r}, current={self.current!r})"


@public
class PathContext(Context):
    """Context that traces targeted actions."""

    path: List[int]
    current: List[int]
    current_depth: int
    value: Any

    def __init__(self, path: Sequence[int]):
        """
        Create a :py:class:`PathContext`.

        :param path: The path of an action in the execution tree that will be captured.
        """
        self.path = list(path)
        self.current = []
        self.current_depth = 0
        self.value = None

    def enter_action(self, action: Action) -> None:
        if self.current_depth == len(self.current):
            self.current.append(0)
        else:
            self.current[self.current_depth] += 1
        self.current_depth += 1
        if self.path == self.current[: self.current_depth]:
            self.value = action

    def exit_action(self, action: Action) -> None:
        if self.current_depth != len(self.current):
            self.current.pop()
        self.current_depth -= 1

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.current!r}, depth={self.current_depth!r})"
        )


current: Optional[Context] = None


class _ContextManager:
    def __init__(self, new_context):
        self.new_context = deepcopy(new_context)

    def __enter__(self) -> Optional[Context]:
        global current
        self.old_context = current
        current = self.new_context
        return current

    def __exit__(self, t, v, tb):
        global current
        current = self.old_context


@public
def local(ctx: Optional[Context] = None) -> ContextManager:
    """
    Use a local context.

    :param ctx: If none, current context is copied.
    :return: A context manager.
    """
    if ctx is None:
        ctx = current
    return _ContextManager(ctx)
