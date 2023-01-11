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

Byteparsing is a functional parser combinator for Python, originally motivated by the problem of parsing OpenFOAM files[^1]. These files contain both ASCII and binary data, which makes them hard to parse using traditional tools. Byteparsing became a flexible tool capable of dealing with generic formats.

<!-- In addition to the basic parser architecture, the `byteparsing` package contains a parser for both ASCII and binary OpenFOAM files. -->

# Statement of need

In research there are many software packages that use non-standard data containers for their input and output. This can be a problem when we need to do post-processing, or when we want to embed such a package in a larger data pipeline. In many cases, these non-standard formats have header information in plain text, while the bulk of the data is saved in binary. Chief and motivating example is the OpenFOAM data format. Other common formats are PLY triangle data[^2] or PPM images[^3]. For these cases, there are only few accessible options for parsing and manipulating data in Python. For instance:

- `pyparsing` is the _de facto_ standard for text parsing in Python. It seems to have no features for dealing with binary data though.
- `construct` deals mostly with pure binary data.
- `Kaitai Struct`, `Antlr` both require a large time investment to learn.

The major downside of the remaining binary parser Python packages we could find is that they focus mostly either on parsing network traffic or on data structures that can be described in a fixed declarative language.

We were thus forced to write our own parser, with this list of requirements:

- Easy to program, using concepts similar to those found in other functional parser combinators like `pyparsing`.
- Composable and testable at all levels of complexity.
- Capable of dealing transparently with Python objects that support the buffer protocol (_i.e.:_: memory mapped file access is trivially supported).
- Performant enough, considering the use case where we have small ASCII headers and large contiguous blocks of floating point data.
- Compliant with best practices such as automated unit testing and thorough documentation.

## A note on architecture

Writing functional parser combinators is a staple of functional languages like Haskell or Ocaml [@frost_1989;@hutton_1992]. The paper "Monadic Parsing in Haskell" [@hutton_meijer_1998] gives a complete tutorial on how to write a basic recursive descent parser. Most of what Hutton and Meijer teach, carries over nicely to Python once we take care of a few details. We've replaced some Haskell idioms by features that are considered more 'pythonic'.

An extended description of the architecture can be found in our documentation[^4]. Those readers more interested in starting working right away will probably find our list of examples[^5] very handy.

# Conclusion
In research software it is unfortunately still quite common to encounter non-standard data formats. For those data formats where a mix of ASCII and binary parsing is needed, Byteparsing can make a useful addition to the existing landscape of parser libraries in Python. Development of a parser using Byteparsing can be relatively quick, as it is easy to build up parsers from smaller testable components.

# Acknowledgements
This project was supported by funding from the Netherlands eScience Center and NWO as part of the Joint Call for Energy Research, Project Number CSER.JCER.025. We also want to acknowledge Dr. Nicolas Renaud for his support and suggestions.

# References

<!-- Footnotes -->
[^1]: https://www.openfoam.com/
[^2]: https://parallelwindfarms.github.io/byteparsing/ply.html
[^3]: https://parallelwindfarms.github.io/byteparsing/ppm.html
[^4]: https://parallelwindfarms.github.io/byteparsing/functional.html
[^5]: https://parallelwindfarms.github.io/byteparsing/index.html

<!-- This is part of the template

# Mathematics

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text.

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:

- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.
-->