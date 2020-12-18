from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple, Callable, Union, Optional

from .cursor import Cursor
from .decorator import decorator


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
    return Parser(f)


def bind(p: Parser, f: Callable[[Any], Parser]) -> Parser:
    """Call parser `p` and feed result to function `f`, which should create
    a new parser. Together with `value` this defines a monad on `Parser`."""
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
        return bind(self, g)

    def parse(self, data: bytes):
        (x, _, _) = self(Cursor.from_bytes(data), []).invoke()
        return x
