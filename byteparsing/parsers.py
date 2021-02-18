"""
Parsers
=======

Some general remarks:

`tokenize`
~~~~~~~~~~

The `tokenize` function is an important tool to deal with whitespace. A
tokenized parser first parses whatever it is supposed to, and then whitespace
of some kind (could also include comments). Note however that `tokenize` only
strips *trailing* whitespace.

`char` variants of `many` and `some`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The parsers `many` and `some` take a parser and use it many times to generate a
list of objects.

Say we have a tokenized parser that parses integers called `integer`, then::

    >>> parse_bytes(many(integer), b"1 2 3 4")
    [1, 2, 3, 4]

Now, we have class of characters `ascii_alpha` parsing any latin character::

    >>> parse_bytes(many(ascii_alpha), b"abcd")
    [b'a', b'b', b'c', b'd']

Probably this is not what you wanted. In many cases what we want is not to
parse a sequence of objects but rather allow for a range of characters to
repeat and then read off the entire resulting string in one go.  This is why we
have `many_char`::

    >>> parse_bytes(many_char(ascii_alpha), b"abcd efgh")
    b"abcd"

How this works is that `many_char` flushes the cursor before running, then
parses `ascii_alpha` until that fails. At that point the cursor is again
flushed and the resulting content returned.

If you use the `many_char` parser as part of a larger parser that uses the
cursor selection, you should use `many_char_0`. This does the same as
`many_char` without flushing. As a consequence `many_char_0` *only* moves the
cursor, it doesn't return anything.

Auxiliary stack
~~~~~~~~~~~~~~~

An auxilary stack variable is threaded through to keep bits of information. A
parser may `push` or `pop` values to this stack. The most common use case for
this is to retrieve values from the middle of a sequence.

If we're parsing a delimited list say `(1 2 3 4)` we can use `sequence`::

    >>> parse_bytes(
    ...     sequence(char('('), many(integer), char(')')),
    ...     b"(1 2 3 4)")
    b')'

What happened is that `sequence` returns the value of the last parser in the
list.  to get at the actual juice, we can push the important value and then pop
it at the end.

    >>> parse_bytes(
    ...     sequence(char('('), many(integer) >> push, char(')'), pop()),
    ...     b"(1 2 3 4)")
    [1, 2, 3, 4]

This is not the pretiest thing, but it works.

Config variable
~~~~~~~~~~~~~~~

We may use the auxiliary stack to store a config variable that can be accessed
from any parser. To make this use a bit more user friendly, we define two
functions: :py:func:`with_config` and the :py:func:`use_config` decorator.

Example
-------
We have as input a number and a string. The string is returned in upper-case if
the number is 1::

    @using_config
    def set_case(x, config):
        config["uppercase"] = (x == 1)
        return value(None)

    @using_config
    def get_text(config):
        if config["uppercase"]:
            return many_char(item, lambda x: x.decode().upper())
        else:
            return many_char(item, lambda x: x.decode())

    assert parse_bytes(
        with_config(sequence(integer >> set_cap, get_text())),
        b'0hello') == "hello"
    assert parse_bytes(
        with_config(sequence(integer >> set_cap, get_text())),
        b'1hello') == "HELLO"

Parsers
~~~~~~~
"""

import logging
from typing import Any, Union, List, Optional, Callable
import numpy as np
import functools

from .cursor import Cursor, Buffer
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


def parse_bytes(p: Parser, data: Buffer):
    """Call parser `p` on `data` and returns result."""
    cursor = Cursor.from_bytes(data)
    result, _, _ = p(cursor, []).invoke()
    return result


def sequence(first: Parser, *rest: Parser) -> Parser:
    """Parse `first`, then `sequence(*rest)`. The parser result
    is that of the last parser in the sequence."""
    if rest:
        return first >> (lambda _: sequence(*rest))
    else:
        return first


def named_sequence(**kwargs: Parser) -> Parser:
    """Similar to `sequence`, this parses using all of the arguments in order.
    The result is now a dictionary where the elements are assigned using the
    result of each given parser."""
    @parser
    def g(c: Cursor, a: Any):
        result = {}
        for k, v in kwargs.items():
            x, c, a = v(c, a).invoke()
            if k[0] != "_":
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
    """A parser that always fails with the given message."""
    @parser
    def g(cursor: Cursor, aux: Any):
        raise Failure(msg)
    return g


def optional(p: Parser, default=None):
    """Doesn't fail if the given parser fails, but returns a default value."""
    return choice(p, value(default))


def pop(transfer=lambda x: x):
    """Pops a value off the auxiliary stack. The result may be transformed
    by a `transfer` function, which defaults to the identity function."""
    @parser
    def g(c: Cursor, a: Any):
        try:
            return transfer(a[-1]), c, a[:-1]
        except Exception as e:
            raise Failure(str(e))
    return g


def push(x: Any):
    """Pushes a value to the auxiliary stack."""
    @parser
    def g(c: Cursor, a: List[Any]):
        return None, c, a + [x]
    return g


def set_aux(x: Any):
    """Replace the entire auxiliary stack. Not commonly used."""
    @parser
    def g(c: Cursor, a: Any):
        return None, c, x
    return g


def get_aux():
    """Get the entire auxiliary stack. Not commonly used."""
    @parser
    def g(c: Cursor, a: Any):
        return a, c, a
    return g


def ignore(p: Parser):
    """Runs the given parser, but doesn't mutate the stack."""
    return get_aux() >> (lambda a: sequence(p, set_aux(a)))


def flush(transfer=lambda x: x):
    """Flush the cursor and return the underlying data. The return
    value can be mapped by the optional `transfer` function."""
    @parser
    def g(c: Cursor, a: Any):
        try:
            return transfer(c.content), c.flush(), a
        except ValueError as e:
            raise Failure(str(e))
    return g


def flush_decode():
    """Flush the cursor and return the underlying data as a decoded
    string."""
    @parser
    def g(c: Cursor, a: Any):
        return c.content_str, c.flush(), a
    return g


def many(p: Parser, init: Optional[List[Any]] = None) -> Parser:
    """Parse `p` any number of times."""
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
    """Parse `p` one or more times."""
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
    """Parse `p` zero or more times, returns the string."""
    return sequence(flush(), many_char_0(p), flush(transfer))


def sep_by(p: Parser, sep: Parser) -> Parser:
    """Parse `p` separated by `sep`. Returns list of `p`."""
    return p >> (lambda first: many(sequence(sep, p))
                 >> (lambda rest: value([first] + rest)))


def text_end_by(x: str) -> Parser:
    @parser
    def g(c: Cursor, a: Any):
        y = x.encode(c.encoding)
        new_cursor = c.find(y)
        result = new_cursor.content_str
        return result, new_cursor.increment(len(y)).flush(), a
    return g


def quoted_string(quote='"'):
    """Parses a quoted string, no quote escaping implemented yet."""
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
    """Parses a single character passing a given predicate."""
    def f(x):
        if pred(x):
            return value(x)
        else:
            raise Failure(f"Character '{chr(x)}' fails predicate"
                          " `{pred.__name__}`")

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


def satisfies(p: Parser, pred) -> Parser:
    def sat_filter(v):
        if pred(v):
            return value(v)
        else:
            raise Failure(f"Unexpected {v}")

    return p >> sat_filter


def byte_one_of(x: bytes) -> Parser:
    return satisfies(item, lambda y: y in x)


def byte_none_of(x: bytes) -> Parser:
    """Parses none of the characters in `x`."""
    return satisfies(item, lambda y: y not in x)


def repeat_n(p: Parser, n: int) -> Parser:
    @parser
    def repeated(c: Cursor, a: Any):
        result = []
        for i in range(n):
            x, c, a = p(c, a).invoke()
            result.append(x)
        return result, c, a
    return repeated


whitespace = some_char(text_one_of(" \t\n"))
eol = choice(text_literal("\n"), text_literal("\n\r"))
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
            result = np.frombuffer(c.data, dtype=dtype, count=size,
                                   offset=c.end)
        except ValueError as e:
            raise Failure(str(e))
        return result, c.increment(result.nbytes), a

    return array_p


def binary_value(dtype: np.dtype):
    """Parses a single binary value of the given `dtype`."""
    return array(dtype, 1) >> fmap(lambda x: x[0])


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


def fmap(f):
    """Maps a parsed value by a function `f`.

        >>> parse_bytes(text_literal("hello") >> fmap(lambda x: x.upper()), b"hello")
        "HELLO"
    """
    return lambda x: value(f(x))


def construct(f):
    """Construct an object `f` by passing a dictionary as keyword arguments. Use this
    in conjunction with `named_sequence`.

        >>> @dataclass
        ... class Point:
        ...     x: float
        ...     y: float

        >>> point = named_sequence(
        ...     _1=tokenize(char("(")),
        ...     x=tokenize(scientific_number),
        ...     _2=tokenize(char(","))
        ...     y=tokenize(scientific_number),
        ...     _3=tokenize(char(")"))
        ...     ) >> construct(Point)

        >>> parse_bytes(point, "(1, 2)")
        Point(x=1, y=2)
    """
    return lambda kwargs: value(f(**kwargs))

