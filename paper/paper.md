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

In research there are many software packages that use non-standard data containers for their input and output. This can be a problem when we need to do post-processing, or when we want to embed such a package in a larger data pipeline. In many cases, these non-standard formats have header information in plain text, while the bulk of the data is saved in binary. For these cases, there are only few accessible options for parsing and manipulating data in Python.

Here are some Python modules for parsing that one could consider:

- `pyparsing` is the _de facto_ standard for text parsing in Python. It seems to have no features for dealing with binary data though.
- `construct` deals mostly with pure binary data
- `Kaitai Struct`
- `antlr` requires a large time investment to learn

The major downside of the other binary parser packages in Python that we could find, is that they focus mostly on parsing network traffic, or data structures that can be described in a fixed declarative language.

The approach we take is:

- Easy to program, using concepts similar to those found in other functional parser combinators like `pyparsing`.
- Deals transparently with Python objects that support the buffer protocol (_e.g._: memory mapped file access is trivially supported).
- Performant enough, considering the use case where we have small ASCII headers and large contiguous blocks of floating point data.

# Architecture

## Functional parser combinators

Writing functional parser combinators is a staple of functional languages like Haskell. The paper "Monadic Parsing in Haskell" [@hutton_meijer_1998] gives a complete tutorial on how to write a basic recursive descent parser. Most of what Hutton and Meijer teach carries over nicely to Python, once we take care of a few details. We've replaced some Haskell idioms by features that are considered more 'pythonic'.

We explain the concept of a monadic parser in terms of taking `str` as input for simplicity. Later we will see that we need to make things a bit more complicated.

The core idea of functional parsing is that a parser for some object is a function. This function takes in the input string, and (possibly) returns the parsed object together with the rest of the input. In Python typing parlance this could be written as

```python
T = TypeVar('T')
Parser = Callable[[str], tuple[T, str]]
```

In this type definition we have not yet encoded the possibility that the parser may fail. In most functional languages the return type of the parser would be `tuple[Optional[T], str]`. However, this is where we make our first change: we use **exceptions**. Whenever a parser fails (planned or unplanned), we raise an exception.

The magic of functional parser combinators happens when we start to combine small parsers into larger ones. To achieve this we need to define the `bind` operation that chains two parser together. We could chain two parsers as follows:

```python
def chain(p: Parser[T], q: Parser[U]) -> Parser[tuple[T,U]]:
  def chained(inp: str) -> [tuple[T,U],str]:
    (a, inp) = p(inp)
    (b, inp) = q(inp)
    return ((a,b), inp)
  return chained
```

The `bind` operator does a slightly different thing. It takes the output of one parser and then passes it to a function that then creates the next parser. This way we can chain together any two parsers and forward the collected information as we like. The problem is that this idiom from Haskell (also known as a Monad), doesn't translate too well to Python.

```python
def bind(p: Parser[T], f: Callable[[T], Parser[U]]) -> Parser[U]
  def bound(inp: str) -> tuple[U, str]
    (a, inp) = p(inp)
    return f(a)(inp)
  return bound
```

The problem with using `bind` as central combinator in our scheme is two-fold: it won't perform well and Python doesn't have the nice syntax to work with `bind`. To explain: the `bind` function returns a new function that then calls more functions, so we're eating into stack space. This means we can never use `bind` to build loops. One way around that is to build a trampoline to evaluate function calls step-by-step, enabling a tail-recursion style of programming. In our opinion it is better to work around the problem and define looping constructs using Python primitives such as `for` and `while`.

For the most part, we are forced to define a more opportune set of primitive parsers that we can use in a more pythonic setting. The most important primitives for combining or multiplexing parsers are: `named_sequence` parsing a set of `**kwarg` parsers to a `dict`, `many` for zero or more items, `some` for one or more items, and `choice` for any of a set of parsers. Further on in this paper, we show how these primitives can be used to build a larger parser.

## Cursor object

Instead of strings, our parser works on top of a `Cursor` object that keeps track of two pointers within a buffer. These two pointers reference the beginning and the (exclusive) end of the currently selected range of data. Having a two-ended cursor object prevents a lot of back-tracking when parsing text that can also be captured by more primitive functions in Python, like standard string conversion routines (`float`, `int`, `datetime` functions), or regex matching. Also, this helps us extract large binary blobs from the buffer more easily.

Additionally, the `Cursor` class can be evaluated to a boolean. This boolean is always `True`, unless the buffer is fully consumed (i.e., both pointers coincide at the end of the buffer). This allows us to comfortably loop _"to the end of the data"_ using a `while` statement.

## Memory mapping

# Parser grammar

This package is strongly based on Haskell's syntax and philosophy. But Python is obviously not Haskell. That is to say, there is no nice syntax for monadic actions. In order to solve this issue, we developed a similar grammar for Python. Below, we present a description of such a grammar.

## Combinators

We have `many`, `some` and `choice` among others. The `many` and `some` combinators come in several flavours. Our architecture using two-ended cursors allows for combinators that flush the cursor and ones that don't.

For example, if we're parsing a floating point number, we don't want to flush the cursor until we're sure that we capture the entire value, and then pass that part to the Python builtin `float` function.

## `sequence`

`sequence` expects our parsed elements to be isomorphic with a list.

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
For our 

## Examples of usage

Although we provide a collection of useful parsers, the real power of this package is that it allows for parser composition.
In this section we'll see a few examples about how this is done.

### Parsing an e-mail address

We begin by defining what characters are acceptable on an email:

```python
email_char = choice(
                ascii_alpha_num, 
                ascii_underscore, 
                text_literal("."), 
                text_literal("-")
              )
```

Now, we abstract the information contained in an email as: `[user]@[host]`[^1]

```python
email = named_sequence(
            user=some_char(email_char), # Step 1
            _1=text_literal("@"), # Step 2
            host=some_char(email_char) # Step 3
        )
```

Now we are ready to parse:

```python
parsed = parse_bytes(email, b'p.rodriguez-sanchez@esciencecenter.nl')

print(parsed)

> {'user': b'p.rodriguez-sanchez', 'host': b'esciencecenter.nl'}
```

Notice that the parser created and populated a dictionary for us.

### Parsing a list of e-mail addresses

We can use parser composition to easily reuse what we learned in the previous section and apply it to a list of emails.
Imagine the list of emails is stored as:

```python
data = b"j.hidding@esciencecenter.nl\np.rodriguez-sanchez@esciencencenter.nl"
```

We'll want to identify and end-of-line character.
Keep in mind that they may differ per OS:

```python
eol = choice(text_literal("\n"), text_literal("\n\r"))
```

Our parser is now simply generated by:

```python
list_of_emails = sep_by(email, eol)
```

Let's try it:

```python
parsed = parse_bytes(list_of_emails, data)

parsed
> [{'user': b'j.hidding', 'host': b'esciencecenter.nl'},
   {'user': b'p.rodriguez-sanchez', 'host': b'esciencencenter.nl'}]
```

### Parsing a csv

Let's parse now something as:

```python
data = b"1;-2;3;-4\n5;-6.2;7;-8.1\n9;-10;11;-12"
```

We can first create a parser for a single line.

```python
csvline = sequence(
            sep_by(scientific_number, text_literal(";")) >> push, 
            many(eol), # Just check the eol exists. Don't store it
            pop() # Return pushed content
          )
```

And then combine multiple lines using the `some` combinator:

```python
csv = some(csvline)
```

Let's try it:

```python
parse_bytes(csv, data)

> [[1, -2, 3, -4], [5, -6.2, 7, -8.1], [9, -10, 11, -12]]
```

<!-- Footnotes -->
[^1]: Notice that we ignore the `"@"` by assigning it to the field `"_1"`.
Why not use just `"_"`? Because we need these fields to be unique.
In case we had more than one ignored value, we recommend using `"_1"`, `"_2"`, and so on for the ignored fields.

<!--
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
-->