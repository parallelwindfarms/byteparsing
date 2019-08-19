from byteparsing.trampoline import Call, Trampoline, Parser
from byteparsing.parsers import item, choice, char
from byteparsing.cursor import Cursor

import pytest


class A(Trampoline):
    pass


def test_trampoline():
    a = A()
    with pytest.raises(NotImplementedError):
        a.invoke()


def test_call():
    c = Cursor.from_bytes(b"Hello, World!")
    a = "some unique object"

    assert isinstance(item(c, a), Call)
    assert isinstance(item(c, a)(), tuple)
    assert item(c, a)()[0] == c.at
    assert item(c, a)()[1] == c.increment()
    assert item(c, a)()[2] is a
    assert item(c, a)() == item(c, a).invoke()


def test_choice():
    c = Cursor.from_bytes(b"Hello, World!")
    a = "some other unique object"
    ps = (char('a'), char('b'), char('H'))

    assert isinstance(choice(*ps), Parser)
    assert isinstance(choice(*ps)(c, a), Call)
    x = choice(*ps)(c, a).invoke()
    assert isinstance(x, tuple)
    assert x[0] == c.at
    assert x[1] == c.increment()
