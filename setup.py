#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup  # type: ignore

here = os.path.abspath(os.path.dirname(__file__))

# To update the package version number, edit byteparsing/__version__.py
version = {}
with open(os.path.join(here, 'byteparsing', '__version__.py')) as f:
    exec(f.read(), version)

with open('README.rst') as readme_file:
    readme = readme_file.read()

test_deps = [
    'pytest',
    'mypy',
    'pytest-cov',
    'pytest-flake8',
    'pycodestyle',
    'pytest-mypy']

setup(
    name='byteparsing',
    version=version['__version__'],
    description="Parser for mixed ASCII/binary data",
    long_description=readme + '\n\n',
    author="Johan Hidding",
    author_email='j.hidding@esciencecenter.nl',
    url='https://github.com/parallelwindfarms/byteparsing',
    packages=[
        'byteparsing',
    ],
    include_package_data=True,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='byteparsing',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    test_suite='tests',
    install_requires=['numpy'],
    setup_requires=[
        # dependency for `python setup.py test`
        'pytest-runner',
        # dependencies for `python setup.py build_sphinx`
        'sphinx',
        'sphinx_rtd_theme',
        'recommonmark'
    ],
    tests_require=test_deps,
    extras_require={
        'dev':  ['prospector[with_pyroma]', 'yapf', 'isort'],
        "test": test_deps
    }
)
