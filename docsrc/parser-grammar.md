# Parser grammar

## Primitives

The boundary between what we consider *primitives* and derived parsers can become a bit vague, nevertheless here is a selection of the most important primitive parsers.

`value(x)`
: Always succeeds, doesn't consume input, returns `x`

`fail(msg)`
: Always fails, raises an exception with `msg` as text.

`item`
: Get a single byte from the stream.

`text_literal(str)`
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
: Matches End of Line characters (_i.e.:_ either `\n` or `\n\r`).

`integer`
: Matches an integer value.

`scientific_number`
: Matches a floating point number, possibly in scientific notation.

## Combinators

<!-- This package is strongly based on Haskell's syntax and philosophy. But Python is obviously not Haskell. That is to say, there is no nice syntax for monadic actions. In order to solve this issue, we developed a similar grammar for Python. Below, we present a description of such a grammar. -->
The next question is, how can we combine our primitive parsers? We already listed the main combinators briefly, here we go into a little more detail.

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

`fmap(f)`
: Takes a function `f`, returns a lambda that maps an argument through `f` to a `value` parser. That sounds complicated, but it allows us to pass a parsed result through `f` using the `>>` operator. For an example, see the PPM parser at the end of this paper.

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
We may use the auxiliary stack to store a config variable that can be accessed from any parser. To make this use a bit more user-friendly, we define two functions: `with_config()` and the `@use_config` decorator. Functions decorated with `@use_config` should have the last argument be the `config` variable. The `with_config` parser sets a config dictionary to be the bottom of the auxiliary stack.

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