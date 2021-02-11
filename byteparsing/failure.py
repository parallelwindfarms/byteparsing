"""
Exceptions
==========

A parser can indicate a failure to parse by raising a `Failure`. Most of the
time such a `Failure` is not fatal, since it would be part of a range of parser
choices.  Say we want to parse a number that is either an `int` or a `float`.
First we would try to parse using the `int` parser. If that fails we can try
for a floating point number instead.
"""

from __future__ import annotations


class Failure(Exception):
    """Base class for all parser failures.
    Indicates a failure to parse the input by a specific parser.
    """
    def __init__(self, description):
        self.description = description

    def __str__(self):
        return self.description


class EndOfInput(Failure):
    """Raised when parser reaches end of input."""
    def __init__(self):
        super().__init__("End of input reached.")


class Expected(Failure):
    """Raised to indicate different expectations by a parser."""
    def __init__(self, x, *irritants):
        self.expectation = x
        self.irritants = irritants

    def __str__(self):
        return f"Expected one of: {self.expectation}, got: {self.irritants}"

    def __add__(self, other: Expected):
        return Expected(self.expectation + other.expectation)


class MultipleFailures(Failure):
    """Raised by the `choice` parser if all options fail."""
    def __init__(self, *x):
        super().__init__(f"Failures: {x}")
