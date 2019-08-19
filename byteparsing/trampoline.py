from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple, Callable, Union

from .cursor import Cursor
from .decorator import decorator


@dataclass
class Trampoline:
    def __call__(self):
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


@dataclass
class Call(Trampoline):
    """Stores a delayed call to a parser. Part of the parser trampoline."""
    p: ParserFunction
    cursor: Cursor
    aux: Any

    def __call__(self):
        return self.p(self.cursor, self.aux)


@decorator
def parser(f: ParserFunction):
    return Parser(f)


def bind(p: Parser, f: Callable[[Any], Parser]) -> Parser:
    """Call parser `p` and feed result to function `f`, which should create
    a new parser. Together with `value` this defines a monad on `Parser`."""
    @parser
    def g(cursor, aux):
        result, cursor, aux = p(cursor, aux).invoke()
        print(cursor, aux, result, f(result))
        return f(result)(cursor, aux)

    return g


@dataclass
class Parser:
    """Wrapper for parser functions."""
    f: ParserFunction

    def __call__(self, cursor: Cursor, aux: Any) -> Call:
        return Call(self.f, cursor, aux)

    def __rshift__(self, g: Callable[[Any], Parser]) -> Parser:
        return bind(self, g)
