import pytest
from byteparsing.failure import Failure, EndOfInput
from byteparsing.parsers import (
    value, parse_bytes, item, fail, char, many_char, flush, sequence,
    literal, text_literal, ignore, tokenize, integer, some, scientific_number,
    choice, ascii_alpha_num, ascii_underscore, named_sequence, some_char,
    push, pop, quoted_string, array
)


data = b"Hello, World!"


def test_fail():
    with pytest.raises(Failure):
        parse_bytes(fail("FAIL!"), data)


def test_item():
    assert parse_bytes(item, data) == data[0]


def test_value():
    assert parse_bytes(value(42), b"") == 42


def test_email():
    email_char = choice(ascii_alpha_num, ascii_underscore)
    email = named_sequence(
        user=some_char(email_char),
        server=sequence(text_literal("@"), flush(), some_char(email_char)),
        country=sequence(text_literal("."), flush(), some_char(email_char))
    )
    assert parse_bytes(email, b"pab@rod.es")['user'] == b"pab"
    assert parse_bytes(email, b"pab@rod.es")['server'] == b"rod"
    assert parse_bytes(email, b"pab@rod.es")['country'] == b"es"


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


def test_pop():
    p = sequence(push(0), pop(lambda x: 1/x))
    with pytest.raises(Failure):
        parse_bytes(p, b"")


def test_quoted_string():
    assert parse_bytes(quoted_string('"'), b"\"blahblah\"") == "blahblah"


def test_array():
    import numpy as np
    numbers = np.random.normal(size=128)
    byte_data = numbers.data.tobytes()
    np.testing.assert_array_equal(
        parse_bytes(array(np.dtype(float), 128), byte_data),
        numbers)

    p = named_sequence(
        open=char("("),
        data=array(np.dtype(float), 128),
        close=char(")"))
    mixed_data = b'(' + byte_data + b')'
    np.testing.assert_array_equal(
        parse_bytes(p, mixed_data)["data"],
        numbers)
