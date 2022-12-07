.. byteparsing documentation master file, created by
   sphinx-quickstart on Thu Jun 21 11:07:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to byteparsing's documentation!
==========================================================

Byteparsing is a package for **mixed text and binary** parsing in Python. The main driver for developing this package was to write a parser for binary OpenFOAM files. The binary file format in OpenFOAM is "special". It is the same as the ASCII based text format, except where large blocks of floating point data are concerned.

When **not to use** `byteparsing`:

* You just need to parse some text: use `pyparsing`, it is the industry's standard.

**Do use** `byteparsing` if:

* You need to tinker with large binary OpenFOAM files directly from Python.
* There is a different package that does not adhere to data standards and hacked together its own mixed ASCII/binary file format. You will have to roll out your own parser. Byteparsing can make this easier.

**Coolest feature**:

* Works with :py:mod:`mmap` and :py:mod:`numpy`! This means you can open the file without reading it entirely into memory, change the NumPy array data and the changes are automatically saved to disk.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Introduction <self>
   install
   examples
   ppm
   ply
   functional
   cursors
   parsers
   architecture
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
