# -*- coding: utf-8 -*-

import logging

from .__version__ import __version__  # noqa
from .cursor import Cursor

logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Johan Hidding"
__email__ = "j.hidding@esciencecenter.nl"
__all__ = ["Cursor"]
