from .parsers import (
    tokenize, text_literal, text_end_by,
    choice, sequence, named_sequence, flush, flush_decode,
    many, push, pop,
    char, char_pred
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
