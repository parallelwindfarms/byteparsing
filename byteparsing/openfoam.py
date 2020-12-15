from .parsers import (
    tokenize, text_literal, text_end_by,
    choice, sequence, named_sequence, flush, flush_decode,
    many, push, pop,
    char, char_pred, Parser, integer
)

ascii_alpha = char_pred(lambda c: 64 < c < 91 or 96 < c < 123)
ascii_num = char_pred(lambda c: 48 <= c < 58)
ascii_alpha_num = choice(ascii_alpha, ascii_num)
ascii_underscore = char(95)

block_comment = sequence(
    text_literal("/*"), flush(),
    text_end_by("*/")
)

line_comment = sequence(
    text_literal("//"), flush(),
    text_end_by("\n")
)

identifier = sequence(
    flush(),
    choice(ascii_underscore, ascii_alpha),
    many(choice(ascii_underscore, ascii_alpha, ascii_num)),
    flush_decode()
)

key_value_pair = named_sequence(
    key=tokenize(identifier),
    value=tokenize(text_end_by(";"))
)

dictionary = named_sequence(
    name=tokenize(identifier),
    content=sequence(
        tokenize(text_literal("{")),
        many(key_value_pair) >> push,
        tokenize(text_literal("}")),
        pop())
)


def uniform_value(p: Parser) -> Parser:
    return sequence(tokenize(text_literal("uniform")), p)


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
        tokenize(char(')')), tokenize(char(';')),
        pop())
    simple_list = named_sequence(
        name=tokenize(identifier), data=entries)
    numbered_list = named_sequence(
        name=tokenize(identifier), size=tokenize(integer), data=entries)
    full_list = named_sequence(
        name=tokenize(identifier), dtype=tokenize(list_type),
        size=tokenize(integer), data=entries)
    return choice(simple_list, numbered_list, full_list)


def nonuniform_value(p: Parser) -> Parser:
    return sequence(tokenize(text_literal("nonuniform")), foam_list(p))


def vector(p: Parser) -> Parser:
    return sequence(
        tokenize(text_literal("(")),
        many(tokenize(p)) >> push,
        tokenize(text_literal(")")),
        pop())
