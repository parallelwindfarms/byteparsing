---
title: 'byteparser: a functional parser combinator for mixed ASCII/binary data'
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

<!-- TODO: consider this title:
byteparsing: a Haskell-flavoured parser for Python 
  JH: I've changed the current title slightly, but I don't think we should advertise a Haskell origin. -->
# Summary

<!-- TODO: write summary -->

In addition to the basic parser architecture, the `byteparsing` package contains a parser for both ASCII and binary OpenFOAM files.

# Statement of need

In research there are many software packages that use non-standard data containers for their input and output. This can be a problem when we need to do post-processing, or when we want to embed such a package in a larger data pipeline. In many cases, these non-standard formats have header information in plain text, while the bulk of the data is saved in binary. Chief and motivating example is the OpenFOAM data format. Other more common formats include PLY triangle data or PPM images. For these cases, there are only few accessible options for parsing and manipulating data in Python.

Here are some Python modules for parsing that one could consider:

- `pyparsing` is the _de facto_ standard for text parsing in Python. It seems to have no features for dealing with binary data though.
- `construct` deals mostly with pure binary data.
- `Kaitai Struct`, `Antlr` both require a large time investment to learn.

The major downside of the remaining binary parser packages in Python we could find is that they focus mostly either on parsing network traffic or on data structures that can be described in a fixed declarative language.

We were thus forced to write our own parser, with this list of requirements:

- Easy to program, using concepts similar to those found in other functional parser combinators like `pyparsing`.
- Composable and testable at all levels of complexity.
- Deals transparently with Python objects that support the buffer protocol (_e.g._: memory mapped file access is trivially supported).
- Performant enough, considering the use case where we have small ASCII headers and large contiguous blocks of floating point data.
<!-- - And last but not least, bloggy languange -->
- Compliant with best practices such as automated unit testing and thorough documentation.

# Architecture

## Functional parser combinators

Writing functional parser combinators is a staple of functional languages like Haskell. The paper "Monadic Parsing in Haskell" [@hutton_meijer_1998] gives a complete tutorial on how to write a basic recursive descent parser. Most of what Hutton and Meijer teach carries over nicely to Python, once we take care of a few details. We've replaced some Haskell idioms by features that are considered more 'pythonic'.

We explain the concept of a functional parser combinator in terms of taking `str` as input for simplicity. Later we will see that we need to make things a bit more complicated.

The core idea of functional parsing is that a parser for some object is a function. This function takes in the input string, and (possibly) returns the parsed object together with the rest of the input. In Python typing parlance this could be written as

```python
T = TypeVar('T')
Parser = Callable[[str], tuple[T, str]]
```

In this type definition we have not yet encoded the possibility that the parser may fail. In most functional languages the return type of the parser would be `tuple[Optional[T], str]`. However, this is where we make our first change: we use **exceptions**. Whenever a parser fails (planned or unplanned), we raise an exception.

Some primitive parsers that we have defined are: `item` for parsing a single byte, `char_pred` for parsing classes of characters, `literal` for parsing string literals and `array` for parsing binary arrays of given type and size.

The magic of functional parser combinators happens when we start to combine small parsers into larger ones. To achieve this we need to define the `bind` operation that chains two parser together. We could chain two parsers as follows:

```python
def chain(p: Parser[T], q: Parser[U]) -> Parser[tuple[T,U]]:
  def chained(inp: str) -> [tuple[T,U],str]:
    (a, inp) = p(inp)
    (b, inp) = q(inp)
    return ((a,b), inp)
  return chained
```

The `bind` operator does a slightly different thing. It takes the output of one parser and then passes it to a function that then creates the next parser. This way we can chain together any two parsers and forward the collected information as we like. The problem is that this idiom from Haskell (also known as a monad), doesn't translate too well to Python. We can still define the `bind` function:

```python
def bind(p: Parser[T], f: Callable[[T], Parser[U]]) -> Parser[U]
  def bound(inp: str) -> tuple[U, str]
    (a, inp) = p(inp)
    return f(a)(inp)
  return bound
```

The problem with using `bind` as central combinator in our scheme is two-fold: it won't perform well and Python doesn't have the nice syntax to work with `bind`. To explain: the `bind` function returns a new function that then calls more functions, so we're eating into stack space. This means we can never use `bind` to build loops. One way around that is to build a trampoline to evaluate function calls step-by-step, enabling a tail-recursion style of programming. In our opinion it is better to work around the problem and define looping constructs using Python primitives such as `for` and `while`.

For the most part, we are forced to define a more opportune set of primitive combinators that we can use in a more pythonic setting. The most important primitives for combining or multiplexing parsers are: `named_sequence` parsing a set of `**kwarg` parsers to a `dict`, `many` for zero or more items, `some` for one or more items, and `choice` for any of a set of parsers. Further on in this paper, we show how these primitives can be used to build a larger parser. That being said, we do define the `bind` function in our parser and also make it usable through the shift-right `>>` operator. There are indeed some cases where this operator lets us write consise and readable code.

## Cursor object

Instead of strings, our parser works on top of a `Cursor` object that keeps track of two pointers within a buffer. These two pointers reference the beginning and the (exclusive) end of the currently selected range of data. Having a two-ended cursor object prevents a lot of back-tracking when parsing text that can also be captured by more primitive functions in Python, like standard string conversion routines (`float`, `int`, `datetime` functions), or regex matching. Also, this helps us extract large binary blobs from the buffer more easily.

Most parsers should, when successful, *flush* the cursor to a state where the begin and end pointers coincide. Suppose we want to parse a (ASCII) floating point number. We can have a parser that accepts digits, dots, hyphens and the letter E. Then the cursor gets to a state where the begin and end pointers straddle the item that we think is a floating point number. We then pass that content through the `float` function, after which we flush the cursor. This releaves us from the tedious task of writing an actual floating point number parser. We are just delimiting interesting points in the buffer, a process also referred to as *lexing*.

Additionally, the `Cursor` class can be evaluated to a boolean. This boolean is always `True`, unless the buffer is fully consumed (i.e., both pointers coincide at the end of the buffer). This allows us to comfortably loop _"to the end of the data"_ using a `while` statement.

The `Cursor` object has a text encoding set, so that we can interact seamlessly with strings.

## Auxiliary state
The parsers in our design also carry an auxiliary state variable, that can be used to temporarily store intermediate results. The variable is forwarded through every parser call. The full type of a parser then becomes:

```python
T = TypeVar('T')
Parser = Callable([Cursor, Any], tuple[T, Cursor, Any])
```

We define two helper functions to make use of the auxiliary state: `push` and `pop`. These assume that the auxiliary state contains a list of items that we can use as a stack. Another application that we have for the auxiliary state, is to store a configuration dictionary. For instance, we can read from a header wether the rest of a file should be read in ASCII or binary format. That information we store in the config, to be retrieved when needed later on.

## Memory mapping

The `Cursor` object acts on top of any object in Python that conforms to the buffer interface. This can be a `bytes` or `bytearray` object, but also `mmap`. This means we can parse memory mapped data directly to buffered numpy arrays (using `numpy.frombuffer`). Changes made to such an array are then directly reflected on the filesystem.

# Parser grammar

## Primitives

The boundary between what we consider *primitives* and derived parsers can become a bit vague, nevertheless here is a selection of the most important primitive parsers.

`value(x)`
: Always succeeds, doesn't consume input, returns `x`

`fail(msg)`
: Always fails, raises an exception with `msg` as text.

`item`
: Get a single byte from the stream.

`literal(str)`
: Succeeds if the next characters in the stream exactly match `str`.

`char_pred(pred)`
: Advances the end of the cursor if `pred` succeeds.

`text_end_by(char)`
: Advances the end of the cursor as until `char` is found.

`push(x)`
: Push a value on the auxiliary stack.

`pop()`
: Pop a value from the auxiliary stack.

We also defined some derived parsers that should be useful in most contexts.

`whitespace`
: Matches tabs spaces and newlines.

`eol`
: Matches either `\n` or `\n\r`.

`integer`
: Matches an integer value.

`scientific_number`
: Matches a floating point number, possibly in scientific notation.

## Combinators

<!-- This package is strongly based on Haskell's syntax and philosophy. But Python is obviously not Haskell. That is to say, there is no nice syntax for monadic actions. In order to solve this issue, we developed a similar grammar for Python. Below, we present a description of such a grammar. -->
We already saw that we defined some primitive parsers. The next question is how can we combine them? We already listed the main combinators briefly, here we go into a little more detail.

`choice(*p)`
: Tries every parser `p` in sequence until one succeeds. If all fail, `choice` gathers all exceptions and composes an error message from that.

`sequence(*p)`
: Runs every parser `p` in sequence and only returns the result of the last one.

`named_sequence(**p)`
: Runs every parser `p` in sequence and stores results in a dictionary. Keys that start with an underscore are not stored.

`many(p)`
: Runs the parser `p` until it fails. Returns a list of parsed items.

`some(p)`
: Parses `p` at least one time, or fail.

The `many` and `some` combinators come in several flavours. Both have a variant called `many_char` and `some_char` that return a string instead of a list. One more flavour is `many_char_0` and `some_char_0` that do not flush the cursor.

Some derived combinators help us shape a little language to describe grammars.

`optional(p, default=None)`
: Parses `p` or gives the default value.

`tokenize(p)`
: Parses `p` followed by optional whitespace. This makes sure we always start at the next token.

### `named_sequence` and `construct`

The `named_sequence` combinator forms a particularly useful pair with the `construct` function. Used on its own, the `named_sequence` creates a dictionary. Many times when we're parsing, we want our results to form some class. The `construct` function takes a dictionary and constructs an object by forwarding the dictionary as keyword arguments.

```python
@dataclass
Point:
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
parse_bytes(point, b"(1, 2)")
```

gives `Point(x=1, y=2)` as output.

### `using_config` and `with_config`
We may use the auxiliary stack to store a config variable that can be accessed from any parser. To make this use a bit more user friendly, we define two functions: `with_config()` and the `@use_config` decorator. Functions decorated with `@use_config` should have the last argument be the `config` variable. The `with_config` parser sets a config dictionary to be the bottom of the auxiliary stack.

Example: We have as input a number and a string. The string is returned in upper-case if the number is 1:

```python
@using_config
def set_case(x, config):
    config["uppercase"] = (x == 1)
    return value(None)

@using_config
def get_text(config):
    if config["uppercase"]:
        return many_char(item, lambda x: x.decode().upper())
    else:
        return many_char(item, lambda x: x.decode())

assert parse_bytes(
    with_config(sequence(integer >> set_case, get_text())),
    b'0hello') == "hello"
assert parse_bytes(
    with_config(sequence(integer >> set_case, get_text())),
    b'1hello') == "HELLO"
```
 

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
parse_bytes(email, b'p.rodriguez-sanchez@esciencecenter.nl')
# returns {'user': b'p.rodriguez-sanchez', 'host': b'esciencecenter.nl'}
```

Notice that the parser created and populated a dictionary for us.

### Parsing a list of e-mail addresses

We can use parser composition to easily reuse what we learned in the previous section and apply it to a list of emails.
Imagine the list of emails is stored as a newline-separated list:

```python
data = b"j.hidding@esciencecenter.nl\np.rodriguez-sanchez@esciencencenter.nl"
```

We'll want to identify and end-of-line character. Keep in mind that they may differ per OS:

```python
eol = choice(text_literal("\n\r"), text_literal("\n"))
```

Our parser is now generated by:

```python
list_of_emails = sep_by(email, eol)
```

This shows how we can slowly compose small and testable parsers to form larger more complicated ones. This composability and testability of each step is what make parser combinators such a powerful tool.

### Binary example: PPM files
As a final example, we show how we can mix ASCII and binary data. Here we parse Portable PixMap files (PPM). These files have a small ASCII header and the image itself in binary. The header looks something like this:

```
P6   # this marks the file type in the Netpbm family
640 480
255
<<binary rgb values: 3*w*h bytes>>
```

This example has the following imports:

```python
import numpy as np
from dataclasses import dataclass
from byteparsing import parse_bytes
from byteparsing.parsers import (
    text_literal, integer, eol, named_sequence, sequence, construct,
    tokenize, item, array,  fmap, text_end_by, optional)
```

The header of the PPM may contain a comment on the first line.

```python
comment = sequence(text_literal("#"), text_end_by("\n"))
```

We define a class that should contain all the data in the header.

```python
@dataclass
class Header:
  width: int
  height: int
  maxint: int
```

Then we can construct a parser for this header, like we have seen, using `named_sequence` and `construct`.

```python
header = named_sequence(
  _1 = tokenize(text_literal("P6")),
  _2 = optional(comment),
  width = tokenize(integer),
  height = tokenize(integer),
  maxint = integer,
  _3 = item) >> construct(Header)
```

We'll have to pass on the header information to the parser for the binary blob somehow, so we define a function.

```python
def image_bytes(header: Header):
    shape = (header.height, header.width, 3)
    size = header.height * header.width * 3
    return array(np.uint8, size) >> fmap(lambda a: a.reshape(shape))
```

Now, the entire parser for a PPM file is one more line.

```python
ppm_image = header >> image_bytes
```

<!-- TODO: add concluding remarks -->

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