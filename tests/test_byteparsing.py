#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the byteparsing module.
"""
import pytest

# from byteparsing import byteparsing


def test_something():
    assert True


def test_with_error():
    with pytest.raises(ValueError):
        # Do something that raises a ValueError
        raise(ValueError)


# Fixture example
@pytest.fixture
def an_object():
    return {}


def test_byteparsing(an_object):
    assert an_object == {}
