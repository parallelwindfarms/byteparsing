from dataclasses import dataclass
from typing import Union
import mmap


@dataclass
class Cursor:
    """Encapsulates a byte string and two offsets to reference the input
    data."""
    data: Union[bytes, bytearray, mmap.mmap]
    begin: int
    end: int
    encoding: str = "utf-8"

    def __bool__(self):
        """`False` if the cursor refererences the end of input, `True`
        otherwise."""
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
        return self.data[self.end:self.end+n]

    def increment(self, n: int = 1):
        """Creates new cursor where end is incremented by `n`."""
        return Cursor(self.data, self.begin, self.end+n)

    def flush(self):
        """Creates new cursor where begin is flushed to end location."""
        return Cursor(self.data, self.end, self.end)

    def find(self, x: bytes):
        return Cursor(self.data, self.begin, self.data.find(x, self.end))
