# -*- coding: utf-8 -*-

import logging

from .__version__ import __version__  # noqa
from .cursor import Cursor
from .trampoline import (Parser, parser)
from .parsers import (
    parse_bytes, sequence, push, pop, char,
    flush, flush_decode,
    many_char, many_char_0, some_char, some_char_0,
    ascii_alpha, fail
    )

try:
    from .openfoam import foam_file
except ImportError:
    foam_file = fail("The OpenFOAM parser needs Numpy.")

logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Johan Hidding"
__email__ = "j.hidding@esciencecenter.nl"
__all__ = ["Cursor", "parse_bytes", "sequence", "push", "pop",
           "flush", "flush_decode", "many_char", "many_char_0",
           "some_char", "some_char_0",
           "char", "ascii_alpha", "foam_file",
           "Parser", "parser"]
