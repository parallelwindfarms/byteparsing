from byteparsing.decorator import decorator
import pytest


def test_decorator():
    @decorator
    def flowers(f):
        return f

    with pytest.raises(TypeError):
        @flowers(3)
        def g():
            pass

    with pytest.raises(TypeError):
        @flowers(3, 9)
        def h():
            pass

    @decorator
    def wallpaper(f, color):
        return lambda: color

    @wallpaper(color="red")
    def i():
        pass

    assert i() == "red"
