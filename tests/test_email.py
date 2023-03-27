from dataclasses import dataclass
from byteparsing.parsers import \
    (ascii_alpha, sequence, named_sequence, text_literal, sep_by, fmap, construct,
     value, fail, flush_decode, flush, some_char_0)

@dataclass
class Email:
    username: str
    domain: list[str]

    def __str__(self):
        joint_domain = ".".join(self.domain)
        return f"{self.username}@{joint_domain}"

# This parser assumes all email characters to fall within ASCII range.
email_comp = sequence(some_char_0(ascii_alpha), flush_decode())

def string(x: str):
    return sequence(text_literal(x), flush())

def guard(pred, msg: str):
    """Guard a parser by a given predicate."""
    def assertion_p(v):
        if pred(v):
            return value(v)
        else:
            return fail(msg)
    return assertion_p

email = named_sequence(
    username=sep_by(email_comp, string(".")) >> fmap(".".join),
    _1=string("@"),
    domain=sep_by(email_comp, string(".")) >> \
        guard(lambda x: len(x) >= 2, "a domain needs at least two components"),
) >> construct(Email)

def test():
    email1 = b"john.steinbeck@grapes.ny"
    assert email.parse(email1) == Email("john.steinbeck", ["grapes", "ny"])