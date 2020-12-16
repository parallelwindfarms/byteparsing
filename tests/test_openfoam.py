import pytest
from pathlib import Path

from byteparsing.failure import (
    Failure
)

from byteparsing.parsers import (
    parse_bytes,
    scientific_number
)

from byteparsing.openfoam import (
    block_comment,
    identifier,
    key_value_pair,
    vector,
    preamble,
    foam_file,
    dimensions,
    foam_list,
    foam_numeric,
    dictionary
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
        "key": "alpha", "value": 1}


def test_vector():
    assert parse_bytes(vector(scientific_number), b"(3.4 10 5e10)") \
        == [3.4, 10, 5e10]


def test_dimensions():
    assert parse_bytes(dimensions, b"[0 2 -2 0 0 0 0]") \
        == [0, 2, -2, 0, 0, 0, 0]


def test_simple_list():
    assert parse_bytes(foam_list(foam_numeric), b"hello (1 2 3 4 5)") \
        == {"name": "hello", "data": [1, 2, 3, 4, 5]}


def test_nested_dict():
    assert parse_bytes(dictionary, b"{ a 5; b 6; c { d (3 4 5); e {} } }") \
        == {"a": 5, "b": 6, "c": {"d": [3, 4, 5], "e": {}}}


def test_preamble():
    test_file = Path(".") / "tests" / "data" / "ascii_scalar"
    data = test_file.open(mode="rb").read()
    assert parse_bytes(preamble, data) == {
        "name": "FoamFile",
        "content": {
            "version": 2.0,
            "format": "ascii",
            "class": "volScalarField",
            "location": "1",
            "object": "p"
        }
    }


def test_ascii_scalar():
    test_file = Path(".") / "tests" / "data" / "ascii_scalar"
    data = test_file.open(mode="rb").read()
    x = parse_bytes(foam_file, data)
    assert x["preamble"] == {
        "name": "FoamFile",
        "content": {
            "version": 2.0,
            "format": "ascii",
            "class": "volScalarField",
            "location": "1",
            "object": "p"
        }
    }
    print(x["data"])
    assert x["data"]["internalField"]["size"] == 10
    assert len(x["data"]["internalField"]["data"]) == 10
