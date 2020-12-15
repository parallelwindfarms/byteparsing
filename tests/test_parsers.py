import pytest
from byteparsing.failure import Failure, EndOfInput
from byteparsing.parsers import (
    value, parse_bytes, item, fail, char, many_char, flush, sequence,
    literal, text_literal, ignore, tokenize, integer, some, scientific_number
)

data = b"Hello, World!"


def test_fail():
    with pytest.raises(Failure):
        parse_bytes(fail("FAIL!"), data)


def test_item():
    assert parse_bytes(item, data) == data[0]


def test_value():
    assert parse_bytes(value(42), b"") == 42


def test_end_of_input():
    with pytest.raises(EndOfInput):
        parse_bytes(item, b"")


def test_sequence():
    p1 = sequence(*(char(c) for c in data), flush())
    assert parse_bytes(p1, data) == data

    p2 = sequence(*(char(c) for c in data), item, flush())
    with pytest.raises(EndOfInput):
        parse_bytes(p2, data)


def test_many_char():
    assert parse_bytes(many_char(item), data) == data


def test_literal():
    assert parse_bytes(literal(data), data) == data
    with pytest.raises(Failure):
        parse_bytes(literal(b"Hello, Universe!"), data)


def test_text_literal():
    assert parse_bytes(text_literal("Hello"), data) == b"Hello"
    assert parse_bytes(ignore(text_literal("Hello")), data) is None
    with pytest.raises(Failure):
        parse_bytes(text_literal("Hi"), data)


def test_tokenize():
    assert parse_bytes(some(tokenize(integer)), b"3 42 -67") == [3, 42, -67]


def test_scientific():
    assert parse_bytes(scientific_number, b"3.1415") == pytest.approx(3.1415)
    with pytest.raises(Failure):
        parse_bytes(scientific_number, b".890")
    with pytest.raises(Failure):
        parse_bytes(scientific_number, b"8.78e78.2")
