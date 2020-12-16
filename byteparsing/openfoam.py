from .parsers import (
    text_literal, text_end_by,
    choice, sequence, named_sequence, flush, flush_decode,
    many, push, pop, fail, value, some,
    char, char_pred, Parser, integer, scientific_number, optional, whitespace,
    quoted_string
)

def latin_char(c):
    return 64 < c < 91 or 96 < c < 123

def number_char(c):
    return 48 <= c < 58

ascii_alpha = char_pred(latin_char)
ascii_num = char_pred(number_char)
ascii_alpha_num = choice(ascii_alpha, ascii_num)
ascii_underscore = char('_')

block_comment = sequence(
    text_literal("/*"), flush(),
    text_end_by("*/")
)

line_comment = sequence(
    text_literal("//"), flush(),
    text_end_by("\n")
)

def tokenize(p: Parser) -> Parser:
    """Parses `p`, clearing surrounding whitespace and comments."""
    return sequence(
        p >> push,
        many(choice(whitespace, block_comment, line_comment)),
        pop())

identifier = sequence(
    flush(),
    choice(ascii_underscore, ascii_alpha),
    many(choice(ascii_underscore, ascii_alpha, ascii_num)),
    flush_decode()
)


def vector(p: Parser) -> Parser:
    return sequence(
        tokenize(text_literal("(")),
        many(tokenize(p)) >> push,
        tokenize(text_literal(")")),
        pop())


foam_numeric = tokenize(choice(scientific_number, vector(scientific_number)))

list_type = sequence(
    text_literal("List<"),
    choice(text_literal("scalar"),
           text_literal("vector")) >> push,
    text_literal(">"),
    pop())


def foam_list(p: Parser) -> Parser:
    entries = sequence(
        tokenize(char('(')),
        many(p) >> push,
        tokenize(char(')')),
        pop())
    simple_list = named_sequence(
        name=tokenize(identifier), data=entries)
    numbered_list = named_sequence(
        name=tokenize(identifier), size=tokenize(integer), data=entries)
    full_list = named_sequence(
        name=tokenize(identifier), dtype=tokenize(list_type),
        size=tokenize(integer), data=entries)
    return choice(simple_list, numbered_list, full_list)


dimensions = sequence(
    tokenize(char('[')),
    some(tokenize(integer)) >> push,
    tokenize(char(']')),
    pop())

foam_value = Parser(None)

def handle_compound(x) -> Parser:
    if len(x["rest"]) == 0:
        return value(x["first"])
    else:
        return value([x["first"]] + x["rest"])

foam_compound_value = named_sequence(
    first=tokenize(identifier),
    rest=many(foam_value)) >> handle_compound

foam_value.func = tokenize(
    choice(foam_numeric, quoted_string(), foam_list(foam_numeric),
           dimensions, foam_compound_value)).func

dictionary = Parser(None)

key_value_pair = named_sequence(
    key=tokenize(identifier),
    value=choice(dictionary,
                 sequence(foam_value >> push, tokenize(char(';')), pop()))
)


def key_value_pairs_to_dict(x):
    return {y["key"]: y["value"] for y in x}


def fmap(f):
    return lambda x: value(f(x))

dictionary.func = sequence(
    tokenize(text_literal("{")),
    many(key_value_pair) >> push,
    tokenize(text_literal("}")),
    pop(key_value_pairs_to_dict)
).func

preamble = sequence(
    optional(whitespace),
    many(tokenize(choice(block_comment, line_comment))),
    named_sequence(
        name=tokenize(identifier),
        content=tokenize(dictionary)))

foam_file = named_sequence(
    preamble=preamble,
    data=some(key_value_pair) >> fmap(key_value_pairs_to_dict))
