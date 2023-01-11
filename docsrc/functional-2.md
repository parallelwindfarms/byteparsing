# Functional parser combinators

We explain the concept of a functional parser combinator in terms of taking `str` as input for simplicity. Later we will see that we need to make things a bit more complicated.

The core idea of functional parsing is that a parser for some object is a function. This function takes in the input string, and (possibly) returns the parsed object together with the rest of the input. In Python typing parlance this could be written as

```python
T = TypeVar('T')
Parser = Callable[[str], tuple[T, str]]
```

In this type definition we have not yet encoded the possibility that the parser may fail. In most functional languages the return type of the parser would be `tuple[Optional[T], str]`. However, this is where we make our first change: we use **exceptions**. Whenever a parser fails (planned or unplanned), we raise an exception.

Some primitive parsers that we have defined are: `item` for parsing a single byte, `char_pred` for parsing classes of characters, `literal` for parsing string literals and `array` for parsing binary arrays of given type and size.

The magic of functional parser combinators happens when we start to combine small parsers into larger ones. To achieve this we need to define the `bind` operation that chains two parsers together. We could chain two parsers as follows:

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

The problem with using `bind` as central combinator in our scheme is two-fold: it won't perform well and Python doesn't have the nice syntax to work with `bind`. To explain: the `bind` function returns a new function that then calls more functions, so we're eating into stack space. This means we can never use `bind` to build loops. Our solution around that was to build a trampoline to evaluate function calls step-by-step, enabling a tail-recursion style of programming. In our opinion it is better to work around the problem and define looping constructs using Python primitives such as `for` and `while`.

For the most part, we are forced to define a more opportune set of primitive combinators that we can use in a more pythonic setting. The most important primitives for combining or multiplexing parsers are: `named_sequence` parsing a set of `**kwarg` parsers to a `dict`, `many` for zero or more items, `some` for one or more items, and `choice` for any of a set of parsers. Further on in this paper, we show how these primitives can be used to build a larger parser. That being said, we do define the `bind` function in our parser and also make it usable through the shift-right `>>` operator. There are indeed some cases where this operator lets us write concise and readable code.

## Cursor object

Instead of strings, our parser works on top of a `Cursor` object that keeps track of two pointers within a buffer. These two pointers reference the beginning and the (exclusive) end of the currently selected range of data. Having a two-ended cursor object prevents a lot of back-tracking when parsing text that can also be captured by more primitive functions in Python, like standard string conversion routines (`float`, `int`, `datetime` functions), or regex matching. Also, this helps us extract large binary blobs from the buffer more easily.

Most parsers should, when successful, *flush* the cursor to a state where the begin and end pointers coincide. Suppose we want to parse a (ASCII) floating point number. We can have a parser that accepts digits, dots, hyphens and the letter `E`. Then the cursor gets to a state where the begin and end pointers straddle the item that we think is a floating point number. We then pass that content through the `float` function, after which we flush the cursor. This releases us from the tedious task of writing an actual floating point number parser. We are just delimiting interesting points in the buffer, a process also referred to as *lexing*.

Additionally, the `Cursor` class can be evaluated to a boolean. This boolean is always `True`, unless the buffer is fully consumed (i.e., both pointers coincide at the end of the buffer). This allows us to comfortably loop _"to the end of the data"_ using a `while` statement.

The `Cursor` object has a text encoding set, so that we can interact seamlessly with strings.

## Auxiliary state
The parsers in our design also carry an auxiliary state variable, that can be used to temporarily store intermediate results. The variable is forwarded through every parser call. The full type of a parser then becomes:

```python
T = TypeVar('T')
Parser = Callable([Cursor, Any], tuple[T, Cursor, Any])
```

We define two helper functions to make use of the auxiliary state: `push` and `pop`. These assume that the auxiliary state contains a list of items that we can use as a stack.

Another application that we have for the auxiliary state, is to store a configuration dictionary. For instance, we can read from a header wether the rest of a file should be read in ASCII or binary format. That information we store in the config, to be retrieved when needed later on.

## Memory mapping

The `Cursor` object acts on top of any object in Python that conforms to the buffer interface. This can be a `bytes` or `bytearray` object, but also `mmap`. This means we can parse memory mapped data directly to buffered `numpy` arrays (using `numpy.frombuffer`). Changes made to such an array are then directly reflected on the file system.