from byteparsing import Cursor


def test_cursor():
    data = b"Hello, World!"
    assert Cursor.from_bytes(data) == Cursor(data, 0, 0)

    c = Cursor.from_bytes(data)
    assert c
    assert c.increment().begin == c.begin
    assert c.increment().end == c.end + 1
    assert c.increment().data is c.data
    assert c.at == c.data[0]
    assert c.content == b''
    assert len(c) == 0

    d = c.increment().increment()
    assert d
    assert d.flush().end == d.end
    assert d.flush().begin == d.end
    assert d.flush().data is d.data
    assert d.at == d.data[d.end]
    assert d.content == b'He'
    assert len(d) == 2
    assert len(d.flush()) == 0
    assert d.flush().at == d.at

    while d:
        d = d.increment()
    assert not d
    assert len(d) == len(data)
    assert d.content == data
