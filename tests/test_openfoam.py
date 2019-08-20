import pytest

from byteparsing.failure import (
    Failure
)

from byteparsing.parsers import (
    parse_bytes
)

from byteparsing.openfoam import (
    block_comment,
    identifier,
    key_value_pair
)


def test_block_comment():
    x = "/* Hello, World! */".encode()
    assert parse_bytes(block_comment, x) == " Hello, World! "


def test_identifier():
    assert parse_bytes(identifier, b"thisShouldWork0") \
        == "thisShouldWork0"
    assert parse_bytes(identifier, b"this_should_also_work_1") \
        == "this_should_also_work_1"

    with pytest.raises(Failure):
        parse_bytes(identifier, b"676test")

    assert parse_bytes(identifier, b"call-with-current-continuation") \
        == "call"


def test_key_value_pair():
    assert parse_bytes(key_value_pair, b"alpha 1;") == {
        "key": "alpha", "value": "1"}
