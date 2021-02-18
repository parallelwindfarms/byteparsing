"""
Cursors
=======

A `Cursor` object contains a reference to the buffer (`bytes`, `bytearray` or
`mmap`), together with a `begin` and `end` pointer. While parsing, usually only
the `end` pointer is updated. Certain parsers first lex the input, i.e. find
where a token begins and ends, and then use some function to convert the
selection to a useable object.

An immediate example: we may use the Python built-in `float` function to
convert a string to a floating point number.  Such a routine should then first
`flush` the cursor, so that `begin` and `end` point to the same location. After
passing a number of numeric characters, decimal point, exponent indication etc,
the part that we think represents a floating-point number can be passed to the
`float` function. This saves us the bother of coding floating point conversion
manually.

.. py:data:: Buffer

    Type for the buffer. One of: `bytes`, `bytearray`, `mmap.mmap`.
"""

from dataclasses import dataclass
from typing import Union
import mmap

Buffer = Union[bytes, bytearray, mmap.mmap]


@dataclass
class Cursor:
    """Encapsulates a byte string and two offsets to reference the input
    data."""
    data: Buffer
    begin: int = 0
    end: int = 0
    encoding: str = "utf-8"

    def __bool__(self):
        """`False` if the cursor references the end of input, `True`
        otherwise. 
        Tip: use `while Cursor:` to run until the end of input"""
        return self.end < len(self.data)

    def __len__(self):
        """Length of current selection."""
        return self.end - self.begin

    @staticmethod
    def from_bytes(data):
        """Constructs a `Cursor` object from a byte string. Initialises `begin`
        and `end` fields at 0."""
        return Cursor(data, 0, 0)

    @property
    def content(self):
        """Byte content of current selection."""
        return self.data[self.begin:self.end]

    @property
    def at(self):
        """Next byte (at end location)."""
        return self.data[self.end]

    @property
    def content_str(self):
        """Decoded string content of current selection."""
        return self.content.decode(self.encoding)

    def look_ahead(self, n: int = 1):
        """Get the next `n` bytes."""
        return self.data[self.end:self.end+n]

    def increment(self, n: int = 1):
        """Creates new cursor where end is incremented by `n`."""
        return Cursor(self.data, self.begin, self.end+n)

    def flush(self):
        """Creates new cursor where begin is flushed to end location."""
        return Cursor(self.data, self.end, self.end)

    def find(self, x: bytes):
        """Get a cursor where the `end` position is shifted to the next
        location where `x` is found."""
        return Cursor(self.data, self.begin, self.data.find(x, self.end))
