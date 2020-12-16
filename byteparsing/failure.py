from __future__ import annotations


class Failure(Exception):
    """Indicates a failure to parse the input by a specific parser."""
    def __init__(self, description):
        self.description = description

    def __str__(self):
        return self.description


class EndOfInput(Failure):
    def __init__(self):
        super().__init__("End of input reached.")


class Expected(Failure):
    def __init__(self, x, *irritants):
        self.expectation = x
        self.irritants = irritants

    def __str__(self):
        return f"Expected one of: {self.expectation}, got: {self.irritants}"

    def __add__(self, other: Expected):
        return Expected(self.expectation + other.expectation)


class MultipleFailures(Failure):
    def __init__(self, *x):
        super().__init__(f"Failures: {x}")
