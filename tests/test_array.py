import pytest
np = pytest.importorskip("numpy")

from byteparsing.parsers import (named_sequence, char, parse_bytes, Failure)
from byteparsing.array import (array)

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

    with pytest.raises(Failure):
        parse_bytes(array(np.dtype(float), 129), byte_data)

