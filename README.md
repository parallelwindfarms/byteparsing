# Byteparsing

![Python package](https://github.com/parallelwindfarms/byteparsing/workflows/Python%20package/badge.svg)
[![PyPI version](https://img.shields.io/pypi/v/byteparsing.svg?colorB=blue)](https://pypi.python.org/pypi/byteparsing/)
[![codecov](https://codecov.io/gh/parallelwindfarms/byteparsing/graph/badge.svg)](https://codecov.io/gh/parallelwindfarms/byteparsing)
[![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-orange)](https://fair-software.eu)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4734194.svg)](https://doi.org/10.5281/zenodo.4734194)

Parser for mixed ASCII/binary data. Features:

- Works extremely well with memory-mapped Numpy arrays
- Included parsers:
    - OpenFOAM
    - Examples: PLY, PPM

## Documentation
Our [documentation](https://parallelwindfarms.github.io/byteparsing) explains the architecture behind `byteparsing` and shows some examples of parsing mixed binary and ASCII data.

## Example: PPM files
Byteparsing is a functional parser combinator (recursive descent) library. To show how we can mix ASCII and binary data, we have an example where we parse Portable PixMap files (PPM). These files have a small ASCII header and the image itself in binary. The header looks something like this:

```
P6   # this marks the file type in the Netpbm family
640 480
256
<<binary rgb values: 3*w*h bytes>>
```

The implementation of the parser:

```python
import numpy as np
from dataclasses import dataclass
from byteparsing import parse_bytes
from byteparsing.parsers import (
    text_literal, integer, eol, named_sequence, sequence, construct,
    tokenize, item, array,  fmap, text_end_by, optional)

comment = sequence(text_literal("#"), text_end_by("\n"))

@dataclass
class Header:
    width: int
    height: int
    maxint: int

header = named_sequence(
    _1 = tokenize(text_literal("P6")),
    _2 = optional(comment),
    width = tokenize(integer),
    height = tokenize(integer),
    maxint = tokenize(integer)) >> construct(Header)

def image_bytes(header: Header):
    shape = (header.height, header.width, 3)
    size = header.height * header.width * 3
    return array(np.uint8, size) >> fmap(lambda a: a.reshape(shape))

ppm_image = header >> image_bytes
```

For more, check out the [documentation](https://parallelwindfarms.github.io/byteparsing)!

## Requirements

This package requires Python (>=3.9), and optionally Numpy.

## Installation

### With pip

To install the latest release of byteparsing, do:

```{.console}
pip install byteparsing
```

### Development with Poetry

This project uses Poetry to maintain `pyproject.toml`.

```{.console}
git clone https://github.com/parallelwindfarms/byteparsing.git
cd byteparsing
poetry install
```

Run tests (including coverage) with:

``` {.console}
poetry run pytest
```

### Contributing

If you want to contribute to the development of byteparsing, have a look
at the [contribution guidelines](CONTRIBUTING.rst).

### License

Copyright (c) 2019, Netherlands eScience Center, University of Groningen

Licensed under the Apache License, Version 2.0 (the \"License\"); you
may not use this file except in compliance with the License. You may
obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an \"AS IS\" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

### Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[NLeSC/python-template](https://github.com/NLeSC/python-template).
