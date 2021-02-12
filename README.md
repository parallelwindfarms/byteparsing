# Byteparsing

![Python package](https://github.com/parallelwindfarms/byteparsing/workflows/Python%20package/badge.svg)
[![PyPI version](https://img.shields.io/pypi/v/byteparsing.svg?colorB=blue)](https://pypi.python.org/pypi/byteparsing/)
[![codecov](https://codecov.io/gh/parallelwindfarms/byteparsing/graph/badge.svg)](https://codecov.io/gh//parallelwindfarms/byteparsing)
[![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-orange)](https://fair-software.eu)

Parser for mixed ASCII/binary data. Features:

- Works extremely well with memory-mapped Numpy arrays
- Included parsers:
    - OpenFOAM

The project setup is documented in [a separate
document](project_setup.rst).
See also the [extended tutorial](https://parallelwindfarms.github.io/byteparsing/functional.html).

## Installation

### With pip

To install the latest release of byteparsing, do:

```{.console}
pip install byteparsing
```

### With GitHub

To install the latest version of byteparsing, do:

``` {.console}
git clone https://github.com/parallelwindfarms/byteparsing.git
cd byteparsing
pip install .
```

Run tests (including coverage) with:

``` {.console}
python setup.py test
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
