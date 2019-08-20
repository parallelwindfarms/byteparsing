import logging
from typing import Any, Union, List, Optional

from .cursor import Cursor
from .failure import Failure, EndOfInput, Expected, MultipleFailures
from .trampoline import Parser, parser

logger = logging.getLogger(__name__)


def value(x) -> Parser:
    """Parses to value `x` without taking input."""
    @parser
    def g(cursor, aux):
        return x, cursor, aux

    return g


def parse_bytes(p: Parser, data: bytes):
    """Call parser `p` on `data` and returns result."""
    cursor = Cursor.from_bytes(data)
    result, _, _ = p(cursor, []).invoke()
    return result


def sequence(first: Parser, *rest: Parser) -> Parser:
    if rest:
        return first >> (lambda _: sequence(*rest))
    else:
        return first


@parser
def item(cursor: Cursor, aux: Any):
    """Accept any token; fails at end of input."""
    if cursor:
        return cursor.at, cursor.increment(), aux
    else:
        raise EndOfInput()


def choice(*ps: Parser) -> Parser:
    """Parses using the first parser in `ps` that succeeds."""
    @parser
    def g(cursor: Cursor, aux: Any):
        failures = []
        for p in ps:
            try:
                return p(cursor, aux).invoke()
            except Failure as f:
                failures.append(f)

        raise MultipleFailures(*failures)
    return g


def fail(msg: str) -> Parser:
    @parser
    def g(cursor: Cursor, aux: Any):
        raise Failure(msg)
    return g


def optional(p: Parser, default=None):
    return choice(p, value(default))


def pop(transfer=lambda x: x):
    @parser
    def g(c: Cursor, a: List[Any]):
        return transfer(a[-1]), c, a[:-1]
    return g


def push(x: Any):
    @parser
    def g(c: Cursor, a: List[Any]):
        return None, c, a + [x]
    return g


def set_aux(x: Any):
    @parser
    def g(c: Cursor, a: Any):
        return None, c, x
    return g


def get_aux():
    @parser
    def g(c: Cursor, a: Any):
        return a, c, a
    return g


def ignore(p: Parser):
    return get_aux() >> (lambda a: sequence(p, set_aux(a)))


def flush(transfer=lambda x: x):
    @parser
    def g(c: Cursor, a: Any):
        return transfer(c.content), c.flush(), a
    return g


def many(p: Parser, init: Optional[List[Any]] = None) -> Parser:
    @parser
    def g(c: Cursor, a: Any):
        try:
            result = init or []
            while True:
                x, c, a = p(c, a).invoke()
                result.append(x)
        except Failure:
            return result, c, a
    return g


def some(p: Parser) -> Parser:
    return p >> (lambda x: many(p, [x]))


def many_char_0(p: Parser) -> Parser:
    @parser
    def g(c: Cursor, a: Any):
        try:
            while True:
                _, c, a = p(c, a).invoke()
        except Failure:
            return None, c, a
    return g


def many_char(p: Parser, transfer=lambda x: x) -> Parser:
    return sequence(flush(), many_char_0(p), flush(transfer))


def some_char_0(p: Parser) -> Parser:
    return sequence(p, many_char_0(p))


def some_char(p: Parser, transfer=lambda x: x) -> Parser:
    return sequence(flush(), some_char_0(p), flush(transfer))


def char(c: Union[str, int]) -> Parser:
    if isinstance(c, str):
        c = ord(c)

    def f(x):
        if x == c:
            return value(c)
        else:
            raise Expected(c)

    return item >> f


def literal(x: bytes) -> Parser:
    """Parses the exact sequence of bytes given in `x`."""
    @parser
    def g(c: Cursor, a: Any):
        if c.look_ahead(len(x)) == x:
            return x, c.increment(len(x)), a
        else:
            raise Expected(x)
    return g


def text_literal(x: str) -> Parser:
    """Parses the contents of `x` encoded by the encoding given in the
    cursor."""
    @parser
    def g(c: Cursor, a: Any):
        return literal(x.encode(c.encoding))(c, a)
    return g


def text_one_of(x: str) -> Parser:
    """Parses any of the characters in `x`."""
    @parser
    def g(c: Cursor, a: Any):
        options = [literal(ch.encode(c.encoding)) for ch in x]
        return choice(*options)(c, a)
    return g


whitespace = some_char(text_one_of(" \t\n"))
integer = sequence(
    flush(),
    optional(text_literal("-")),
    text_one_of("123456789"),
    many_char_0(text_one_of("0123456789")),
    flush(int))


def tokenize(p: Parser) -> Parser:
    """Parses `p`, clearing surrounding whitespace."""
    return sequence(
        optional(whitespace), p >> push,
        optional(whitespace), pop())
