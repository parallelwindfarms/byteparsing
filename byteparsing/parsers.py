import logging
from typing import Any, Union, List, Optional, Callable
import numpy as np
import functools
import mmap

from .cursor import Cursor
from .failure import Failure, EndOfInput, Expected, MultipleFailures
from .trampoline import Parser, parser
from .decorator import decorator

logger = logging.getLogger(__name__)


def value(x) -> Parser:
    """Parses to value `x` without taking input."""
    @parser
    def g(cursor, aux):
        return x, cursor, aux

    return g


def parse_bytes(p: Parser, data: Union[bytes, bytearray, mmap.mmap]):
    """Call parser `p` on `data` and returns result."""
    cursor = Cursor.from_bytes(data)
    result, _, _ = p(cursor, []).invoke()
    return result


def sequence(first: Parser, *rest: Parser) -> Parser:
    if rest:
        return first >> (lambda _: sequence(*rest))
    else:
        return first


def named_sequence(**kwargs: Parser) -> Parser:
    @parser
    def g(c: Cursor, a: Any):
        result = {}
        for k, v in kwargs.items():
            x, c, a = v(c, a).invoke()
            result[k] = x
        return result, c, a
    return g


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
        try:
            return transfer(a[-1]), c, a[:-1]
        except Exception as e:
            raise Failure(str(e))
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
        try:
            return transfer(c.content), c.flush(), a
        except ValueError as e:
            raise Failure(str(e))
    return g


def flush_decode():
    @parser
    def g(c: Cursor, a: Any):
        return c.content_str, c.flush(), a
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


def text_end_by(x: str) -> Parser:
    @parser
    def g(c: Cursor, a: Any):
        y = x.encode(c.encoding)
        new_cursor = c.find(y)
        result = new_cursor.content_str
        return result, new_cursor.increment(len(y)).flush(), a
    return g


def quoted_string(quote='"'):
    return sequence(
        char(quote), flush(),
        text_end_by(quote))


def some_char_0(p: Parser) -> Parser:
    """Parses one or more characters; doesn't return a value, just
    moves the cursor for later flushing."""
    return sequence(p, many_char_0(p))


def some_char(p: Parser, transfer=lambda x: x) -> Parser:
    """Parses `p` one or more times."""
    return sequence(flush(), some_char_0(p), flush(transfer))


def char_pred(pred: Callable[[int], bool]) -> Parser:
    """Parses a single character passing `pred`."""
    def f(x):
        if pred(x):
            return value(x)
        else:
            raise Failure(f"Character '{chr(x)}' fails predicate `{pred.__name__}`")

    return item >> f


def char(c: Union[str, int]) -> Parser:
    """Parses a single character maching `c`."""
    if isinstance(c, str):
        c = ord(c)

    def f(x):
        if x == c:
            return value(c)
        else:
            raise Expected(c, x)

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
ascii_alpha = char_pred(lambda c: 64 < c < 91 or 96 < c < 123)
ascii_num = char_pred(lambda c: 48 <= c < 58)
ascii_alpha_num = choice(ascii_alpha, ascii_num)
ascii_underscore = char(95)

integer = sequence(
    flush(),
    optional(text_literal("-")),
    some_char_0(text_one_of("0123456789")),
    flush(int))


def to_number(s: str) -> Union[int, float]:
    try:
        return int(s)
    except ValueError:
        return float(s)


scientific_number = sequence(
    flush(),
    optional(text_literal("-")),
    ascii_num,
    many_char_0(choice(ascii_num, text_one_of(".e-"))),
    flush(to_number))


def check_size(n: int) -> Callable:
    """ Raises an exception if size is not n."""
    def f(lst: list):
        if len(lst) != n:
            raise Failure(f"Expected list of size {n}, got size {len(lst)}")
        return value(lst)
    return f


def tokenize(p: Parser) -> Parser:
    """Parses `p`, clearing surrounding whitespace."""
    return sequence(
        p >> push,
        optional(whitespace), pop())


def array(dtype: np.dtype, size: int) -> Parser:
    """Reads the next `sizeof(dtype) * product(shape)` bytes from the
    cursor and interprets them as numeric binary data."""
    @parser
    def array_p(c: Cursor, a: Any):
        try:
            result = np.frombuffer(c.data, dtype=dtype, count=size, offset=c.end)
        except ValueError as e:
            raise Failure(str(e))
        return result, c.increment(result.nbytes), a

    return array_p


def with_config(p: Parser, **kwargs) -> Parser:
    """Creates a config object at the bottom of the auxiliary stack.
    The config will be a empty dictionary. The resulting parser should
    be the outer-most parser being used."""
    return sequence(set_aux([dict(kwargs)]), p)


@decorator
def using_config(f):
    """Use this decorator to pass the config as a keyword argument to a
    parser generator."""
    @functools.wraps(f)
    def g(*args, **kwargs) -> Parser:
        return get_aux() >> (lambda a: f(*args, **kwargs, config=a[0]))

    return g
