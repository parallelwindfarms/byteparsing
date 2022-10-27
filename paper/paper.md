---
title: 'byteparser: a functional parser for binary and ASCII'
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

# Statement of need
In research there are many software packages that use non-standard data containers for their input and output. This can be a problem when we need to do post-processing, or when we want to embed such a package in a larger data pipeline. In many cases, these non-standard formats have header information in plain text, while the bulk of the data is saved in binary. For these cases, there are only few accesible options for parsing and manipulating data in Python.

Here are some Python modules for parsing that one could consider:
- `pyparsing` is the de-facto standard for text parsing in Python. It seems to have no features for dealing with binary data though.
- `construct` deals mostly with pure binary data
- `Kaitai Struct`
- `antlr` requires a large time investment to learn

The major downside of the other binary parser packages in Python that we could find, is that they focus mostly on parsing network trafic, or data structures that can be described in a fixed declarative language.

The approach we take is:
- Easy to program, using concepts similar to those found in other functional parser combinators like `pyparsing`.
- Deals transparently with Python objects that support the buffer protocol (e.g. memory mapped file access is trivially supported).
- Performant enough, considering the use case where we have small ASCII headers and large contiguous blocks of floating point data.

# Architecture

## Functional parser combinators

## Cursor object
Our parser works on top of a `Cursor` object that keeps track of two pointers within a buffer. These two pointers reference the begining and end (exclusive) of the currently selected range of data. Having a two-ended cursor object prevents a lot of back-tracking when parsing text that can also be captured by more primitive functions in Python, like standard string conversion routines (`float`, `int`, `datetime` functions), or regex matching.

## Memory mapping

# Parser grammar
Because Python is not Haskell, that is to say, there is no nice syntax for monadic actions, we are bound to end up with a different grammar than we have in Haskell.

## Combinators
We have `many`, `some` and `choice` among others. The `many` and `some` combinators come in several flavours. Our architecture using two-ended cursors allows for combinators that flush the cursor and ones that don't. For example, if we're parsing a floating point number, we don't want to flush the cursor until we're sure that we capture the entire value, and then pass that part to the Python builtin `float` function. 

## `sequence`

## `named_sequence` and `construct`
The `named_sequence` is the dictionary backed alternative to `sequence`. Instead of a `list` of parsed items, this returns a `dict` containing the items named as arguments to `named_sequence`. Any keyword argument starting with an underscore is thrown away. We may combine a `named_sequence` with the `construct` function to easily build a hierarchy of dataclasses.

```python
@dataclass Point:
  x: float
  y: float
```

```python
point = named_sequence(
  _1=tokenize(char("(")),
  x=tokenize(scientific_number),
  _2=tokenize(char(","))
  y=tokenize(scientific_number),
  _3=tokenize(char(")"))
  ) >> construct(Point)
```

The `point` parser then constructs `Point` objects, such that

```python
parse_bytes(point, "(1, 2)")
```

gives `Point(x=1, y=2)` as output.

## `using_config` and `with_config`

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

# References
