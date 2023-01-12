---
title: 'byteparsing: a functional parser combinator for mixed ASCII/binary data'
tags:
  - Python
  - parsing
  - binary
  - ascii
  - functional-programming
authors:
  - name: Johan Hidding
    corresponding: true # (This is how to denote the corresponding author)
    equal-contrib: true
    affiliation: 1
    orcid: 0000-0002-7550-1796
  - name: Pablo Rodríguez-Sánchez
    orcid: 0000-0002-2855-940X
    equal-contrib: true
    affiliation: 1
affiliations:
 - name: Netherlands eScience Center
   index: 1
date: 25 October 2022
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
# aas-doi: 10.3847/xxxxx <- update this with the DOI from AAS once you know it.
# aas-journal: Astrophysical Journal <- The name of the AAS journal.
---

# Summary

Byteparsing is a functional parser combinator for Python. It was originally motivated by the problem of parsing OpenFOAM files. OpenFOAM [^1] is a free, open source computational fluid dynamics software whose input and output files contain both ASCII and binary data. Other common formats combining ASCII and binary are PLY triangle data or PPM images[^2]. This makes them particularly hard to parse using traditional tools. Byteparsing became a flexible tool capable of dealing with generic formats.

# Statement of need

There are already a few accessible options for parsing and manipulating data in Python. For instance:

- `pyparsing` is the _de facto_ standard for text parsing in Python. It seems to have no features for dealing with binary data though.
- `construct` deals mostly with pure binary data.
- `Kaitai Struct` and `Antlr` both require a large time investment to learn.

The major downside of the remaining binary parser Python packages we could find is that they focus mostly either on parsing network traffic or on data structures that can be described in a fixed declarative language.

Our research problem, namely, manipulating OpenFOAM files from Python, required a parser with the following characteristics:

- Capable of dealing with files combining ASCII and binary.
- Easy to program, using concepts similar to those found in other functional parser combinators like `pyparsing`.
- Composable and testable at all levels of complexity.
- Capable of dealing transparently with Python objects that support the buffer protocol (_i.e.:_ memory mapped file access is trivially supported).
- Performant enough, considering the use case where we have small ASCII headers and large contiguous blocks of floating point data.
- Compliant with best practices, such as automated unit testing and thorough documentation.

Byteparser is the solution we developed based on this list of requirements.

## A note on architecture

Writing functional parser combinators is a staple of functional languages like Haskell or Ocaml [@frost_1989;@hutton_1992]. The paper "Monadic Parsing in Haskell" [@hutton_meijer_1998] gives a complete tutorial on how to write a basic recursive descent parser. Most of what Hutton and Meijer teach carries over nicely to Python once we take care of a few details. We've replaced some Haskell idioms by features that are considered more 'pythonic'.

An extended description of the concept of functional parser combinators can be found in the documentation[^3]. Those readers more interested in starting working right away will probably find our lists of examples[^4] very practical.

# Conclusion
In research software it is unfortunately still quite common to encounter non-standard data formats. For those data formats where a mix of ASCII and binary parsing is needed, Byteparsing can make a useful addition to the existing landscape of parser libraries in Python. Development of a parser using Byteparsing can be relatively quick, as it is easy to build up parsers from smaller testable components.

# Acknowledgements
This project was supported by funding from the Netherlands eScience Center and NWO as part of the Joint Call for Energy Research, Project Number CSER.JCER.025. We also want to acknowledge Dr. Nicolas Renaud for his support and suggestions.

# References

<!-- Footnotes -->
[^1]: [https://www.openfoam.com/](https://www.openfoam.com/)
[^2]: [https://parallelwindfarms.github.io/byteparsing/advanced.html](https://parallelwindfarms.github.io/byteparsing/advanced.html)
[^3]: [https://parallelwindfarms.github.io/byteparsing/functional.html](https://parallelwindfarms.github.io/byteparsing/functional.html)
[^4]: [https://parallelwindfarms.github.io/byteparsing/examples.html](https://parallelwindfarms.github.io/byteparsing/examples.html)