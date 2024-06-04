"""
Provides classes for tracing the execution of operations.

The operations include key generation, scalar multiplication, formula execution and individual operation evaluation.
These operations are traced in `Context` classes using `Actions`. Different contexts trace actions differently.

A :py:class:`DefaultContext` traces actions into a tree as they are executed (a scalar
multiplication actions has as its children an ordered list of the individual formula executions it has done).

A :py:class:`PathContext` works like a :py:class:`DefaultContext` that only traces an action on a particular path
in the tree.
"""
from abc import abstractmethod, ABC
from copy import deepcopy
from typing import List, Optional, ContextManager, Any, Sequence, Callable

from public import public
from anytree import RenderTree, NodeMixin, AbstractStyle, PostOrderIter


@public
class Action:
    """
    An Action.

    Can be entered:

    >>> with Action() as action:
    ...     print(action.inside)
    True

    """

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

    def __repr__(self):
        return "Action()"


@public
class ResultAction(Action):
    """
    An action that has a result.

    >>> with ResultAction() as action:
    ...     r = action.exit("result")
    >>> action.result == r
    True
    """

    _result: Any = None
    _has_result: bool = False

    @property
    def result(self) -> Any:
        """The result of the action."""
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

    def __repr__(self):
        return f"ResultAction(result={self._result!r})"


@public
class Node(NodeMixin):
    """A node in an execution tree."""

    action: Action
    """The action of the node."""

    def __init__(self, action: Action, parent=None, children=None):
        self.action = action
        self.parent = parent
        if children:
            self.children = children

    def get_by_key(self, path: List[Action]) -> "Node":
        """
        Get a Node from the tree by a path of :py:class:`Action` s.

        >>> tree = Node(Action())
        >>> a_a = Action()
        >>> a = Node(a_a, parent=tree)
        >>> one_a = Action()
        >>> one = Node(one_a, parent=a)
        >>> other_a = Action()
        >>> other = Node(other_a, parent=a)
        >>> tree.get_by_key([]) == tree
        True
        >>> tree.get_by_key([a_a]) == a
        True
        >>> tree.get_by_key(([a_a, one_a])) == one
        True

        :param path: The path of actions to walk.
        :return: The node.
        """
        if len(path) == 0:
            return self
        for child in self.children:
            if path[0] == child.action:
                return child.get_by_key(path[1:])
        raise ValueError("Path not found.")

    def get_by_index(self, path: List[int]) -> "Node":
        """
        Get a Node from the tree by a path of indices.

        >>> tree = Node(Action())
        >>> a_a = Action()
        >>> a = Node(a_a, parent=tree)
        >>> one_a = Action()
        >>> one = Node(one_a, parent=a)
        >>> other_a = Action()
        >>> other = Node(other_a, parent=a)
        >>> tree.get_by_index([]) == tree
        True
        >>> tree.get_by_index([0]) == a
        True
        >>> tree.get_by_index(([0, 0])) == one
        True

        :param path: The path of indices.
        :return: The node.
        """
        if len(path) == 0:
            return self
        return self.children[path[0]].get_by_index(path[1:])

    def walk(self, callback: Callable[[Action], None]):
        """
        Walk the tree in post-order (as it was executed) and apply :paramref:`callback`.

        :param callback: The callback to apply to the actions in the nodes.
        """
        for node in PostOrderIter(self):
            callback(node.action)

    def render(self) -> str:
        """Render the tree."""
        style = AbstractStyle("\u2502  ", "\u251c\u2500\u2500", "\u2514\u2500\u2500")
        return RenderTree(self, style=style).by_attr(lambda node: node.action)

    def __str__(self):
        return self.render()

    def __repr__(self):
        return self.render()


@public
class Context(ABC):
    """
    Context is an object that traces actions which happen.

    There is always one context active, see functions :py:func:`getcontext`,
    :py:func:`setcontext` and :py:func:`resetcontext`. Also, the :py:func:`local`
    contextmanager.
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
    """
    Context that traces executions of actions in a forest.

    >>> with local(DefaultContext()) as ctx:
    ...     with Action() as one_action:
    ...         with ResultAction() as other_action:
    ...             r = other_action.exit("some result")
    ...         with Action() as yet_another:
    ...             pass
    >>> print(ctx.actions[0]) # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
    Action()
    ├──ResultAction(result='some result')
    └──Action()
    >>> for other in ctx.actions[0].children: # doctest: +ELLIPSIS
    ...     print(other.action)
    ResultAction(result='some result')
    Action()
    """

    actions: List[Node]
    """A forest of trees."""
    current: List[Action]
    """The path to the current action."""

    def __init__(self):
        self.actions = []
        self.current = []

    def enter_action(self, action: Action) -> None:
        if not self.actions:
            self.actions.append(Node(action))
        else:
            if self.current:
                root = next(filter(lambda node: node.action == self.current[0], self.actions))
                Node(action, parent=root.get_by_key(self.current[1:]))
            else:
                self.actions.append(Node(action))
        self.current.append(action)

    def exit_action(self, action: Action) -> None:
        if len(self.current) < 1 or self.current[-1] != action:
            raise ValueError("Cannot exit, not in an action.")
        self.current.pop()

    def __repr__(self):
        return f"{self.__class__.__name__}(actions={sum(map(lambda action: action.size, self.actions))}, current={self.current!r})"


@public
class PathContext(Context):
    """Context that traces targeted actions."""

    path: List[int]
    current: List[int]
    current_depth: int
    value: Optional[Action]

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
        # TODO: Is this deepcopy a good idea?
        self.new_context = deepcopy(new_context)

    def __enter__(self) -> Optional[Context]:
        global current  # This is OK, skipcq: PYL-W0603
        self.old_context = current
        current = self.new_context
        return current

    def __exit__(self, t, v, tb):
        global current  # This is OK, skipcq: PYL-W0603
        current = self.old_context


@public
def local(ctx: Optional[Context] = None) -> ContextManager:
    """
    Use a local context.

    Use it like a contextmanager, the context is active during its execution.

    >>> with local(DefaultContext()) as ctx:
    ...     with Action() as action:
    ...         pass
    >>> ctx.actions[0].action == action
    True

    :param ctx: If none, current context is copied.
    :return: A context manager.
    """
    return _ContextManager(ctx)
