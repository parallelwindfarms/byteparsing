import pytest
import numpy as np
from pathlib import Path

from byteparsing.failure import (
    Failure
)

from byteparsing.parsers import (
    parse_bytes,
    scientific_number,
    with_config
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
    assert parse_bytes(vector(scientific_number), b"(3.4 10 -1.2 5e9 -4e-5)") \
        == [3.4, 10, -1.2, 5e9, -4e-5]


def test_dimensions():
    assert parse_bytes(dimensions, b"[0 2 -2 0 0 0 0]") \
        == [0, 2, -2, 0, 0, 0, 0]
    with pytest.raises(Failure):
        # Wrongly formatted dimensions vector
        parse_bytes(dimensions, b"(0 2 -1 0 0 0 0 2)")
    with pytest.raises(Failure):
        # The number of dimensions should be 7
        parse_bytes(dimensions, b"[0 2 -1 0 0 0]")


def test_simple_list():
    assert parse_bytes(with_config(foam_list(), format="ascii"),
                       b"hello (1 2 3 4 5)") \
        == {"name": "hello", "data": [1, 2, 3, 4, 5]}


def test_nested_dict():
    assert parse_bytes(dictionary, b"{ a 5; b 6; c { d (3 4 5); e {} } }") \
        == {"a": 5, "b": 6, "c": {"d": [3, 4, 5], "e": {}}}


def test_preamble():
    test_file = Path(".") / "tests" / "data" / "ascii_scalar"
    data = test_file.open(mode="rb").read()
    assert parse_bytes(with_config(preamble), data) == {
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


def test_ascii_vector():
    test_file = Path(".") / "tests" / "data" / "ascii_vector"
    data = test_file.open(mode="rb").read()
    x = parse_bytes(foam_file, data)
    assert x["preamble"] == {
        "name": "FoamFile",
        "content": {
            "version": 2.0,
            "format": "ascii",
            "class": "volVectorField",
            "location": "1",
            "object": "U"
        }
    }
    print(x["data"])
    assert x["data"]["internalField"]["size"] == 10
    assert len(x["data"]["internalField"]["data"]) == 10
    assert np.array(x["data"]["internalField"]["data"]).shape == (10, 3)


def test_binary_scalar():
    test_file = Path(".") / "tests" / "data" / "binary_scalar"
    data = test_file.open(mode="rb").read()
    x = parse_bytes(foam_file, data)
    assert x["preamble"] == {
        "name": "FoamFile",
        "content": {
            "version": 2.0,
            "format": "binary",
            "class": "volScalarField",
            "arch":  "LSB;label=32;scalar=64",
            "location": "1",
            "object": "p"
        }
    }
    print(x["data"])
    assert x["data"]["internalField"].size == 9200


def test_binary_vector():
    test_file = Path(".") / "tests" / "data" / "binary_vector"
    data = test_file.open(mode="rb").read()
    x = parse_bytes(foam_file, data)
    assert x["preamble"] == {
        "name": "FoamFile",
        "content": {
            "version": 2.0,
            "format": "binary",
            "class": "volVectorField",
            "arch":  "LSB;label=32;scalar=64",
            "location": "1",
            "object": "U"
        }
    }
    print(x["data"])
    assert x["data"]["internalField"].shape == (9200, 3)


def test_modify_data(tmpdir):
    import mmap
    import shutil
    test_path = Path(".") / "tests" / "data" / "binary_scalar"
    shutil.copy(test_path, tmpdir / "testfile")

    test_file = (tmpdir / "testfile").open(mode="r+b")
    mm = mmap.mmap(test_file.fileno(), 0)

    x = parse_bytes(foam_file, mm)
    assert x["preamble"] == {
        "name": "FoamFile",
        "content": {
            "version": 2.0,
            "format": "binary",
            "class": "volScalarField",
            "arch":  "LSB;label=32;scalar=64",
            "location": "1",
            "object": "p"
        }
    }
    print(x["data"])
    assert x["data"]["internalField"].size == 9200

    x["data"]["internalField"][:10] = np.arange(10)
    y = parse_bytes(foam_file, mm)
    np.testing.assert_array_equal(
        y["data"]["internalField"][:10],
        np.arange(10))
