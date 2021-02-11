"""
Trampoline
==========

The trampoline is a pattern for running recursive algorithms on the heap.
A trampolined function returns either another `Trampoline` object or
some result. If we get a `Trampoline` object, the loop continues. This
technique allows for the expression of tail-recursive functions without
running into stack overflow errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple, Callable, Union, Optional

from .cursor import Cursor
from .decorator import decorator


class Trampoline:
    """Base class implementing the trampoline loop structure."""
    def __call__(self):
        """Not implemented: this should be overloaded by the
        derived class."""
        raise NotImplementedError()

    def invoke(self):
        """Invoke the trampoline."""
        result = self
        while isinstance(result, Trampoline):
            result = result()
        return result


ParserFunction = Callable[
    [Cursor, Any],
    Union[Tuple[Any, Cursor, Any], Trampoline]]

# Due to an issue in MyPy (#708) I have to use this workaround.
ParserFunctionIssue708 = Callable[
    ..., Union[Tuple[Any, Cursor, Any], Trampoline]]


@dataclass
class Call(Trampoline):
    """Stores a delayed call to a parser. Part of the parser trampoline."""
    p: ParserFunctionIssue708
    cursor: Cursor
    aux: Any

    def __call__(self) -> Union[Tuple[Any, Cursor, Any], Trampoline]:
        return self.p(self.cursor, self.aux)


@decorator
def parser(f: ParserFunction):
    """The parser decorator creates a parser out of a function with the
    following signature::

        @parser
        def some_parser(cursor: Cursor, aux: Any) -> tuple[T, Cursor, Any]:
            pass

    A parser takes a `Cursor` object and returns a parsed object together
    with the updated cursor. The `aux` object is used to pass around
    auxiliary state.

    This decorator function is an alias for `Parser.__init__`.
    """
    return Parser(f)


def bind(p: Parser, f: Callable[[Any], Parser]) -> Parser:
    """Call parser `p` and feed result to function `f`, which should create
    a new parser. The `Parser` class defines the `>>` operator as an alias for
    `bind`.

    Together with `value` this defines a monad on `Parser`.

    If you are unfamiliar with monads, this function can be a bit hard to
    grasp. However, a tutorial on monads is outside the scope of this
    document.

    The `>>` operator is one of the primary ways of composing parsers
    (the other being `choice`).
    """
    @parser
    def g(cursor, aux):
        result, cursor, aux = p(cursor, aux).invoke()
        return f(result)(cursor, aux)

    return g


@dataclass
class Parser:
    """Wrapper for parser functions."""
    func: Optional[ParserFunctionIssue708]

    def __call__(self, cursor: Cursor, aux: Any) -> Call:
        assert self.func is not None
        return Call(self.func, cursor, aux)

    def __rshift__(self, g: Callable[[Any], Parser]) -> Parser:
        """The `>>` operator is one of the primary ways of composing
        parsers (the other being `choice`)."""
        return bind(self, g)

    def parse(self, data: bytes):
        """DEPRICATED: call `byteparsing.parse_bytes` instead."""
        (x, _, _) = self(Cursor.from_bytes(data), []).invoke()
        return x
