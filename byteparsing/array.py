import numpy as np
from typing import Any

from .cursor import Cursor
from .failure import Failure
from .trampoline import Parser, parser
from .parsers import fmap


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

