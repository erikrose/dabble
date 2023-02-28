import re

from .exceptions import LexError


token_pattern = re.compile(
    # A line that's just whitespace and/or comment:
    r'(?P<skipped_line>^[ \t]*(?:#.*|)$)|'
    r'(?P<dent>^[ \t]*)|'
    r'(?P<horizontal_whitespace>[ \t]+)|'
    r'(?P<word>[-a-zA-Z+*/><=]+)|'
    r'(?P<int>(?:0|[1-9]([0-9])*))|'
#    r'(?P<string>\"[^\"]*")|'
    r'(?P<paren>\()|'
    r'(?P<end_paren>\))|'
    r'(?P<unmatched>.)',
    flags=re.M)


class TokenConst(object):
    """A way of expressing singleton tokens that pretty-prints nicely for
    tests"""

    def __init__(self, identity):
        self.identity = identity

    def __repr__(self):
        return self.identity


# OPEN and CLOSE represent the start and end of a whitespace-delimited list.
# They do not correspond directly to indents and outdents.
OPEN = TokenConst('OPEN')
CLOSE = TokenConst('CLOSE')


def lex(text):
    """Break down a string into an iterable of tokens based on indentation in a
    scheme akin to the I-expressions presented in SRFI 49.

    * The first line of a file (or a line with the same indentation as the
      previous one) is a list.
    * Indenting starts a new list inside the previous one.
    * The list continues until indentation goes back to the pre-indented level.
    * One atom on a line is just an atom, not a 1-list. This will
      keep us from having to overnotate in the branches of ifs, which are
      common. And it will make our unary functions look like OCaml's--``foo
      ()``--which have proven tolerable. We don't want to do exotic things like
      make exceptions based on type (the expression is its own value if not a
      function, a function call if a function), because then you can't write the
      identity function and pass it a function.
    * Both tabs and spaces are considered indentation.
    * Inconsistent indentation is an error. The whitespace characters that make
      up each indent must be either an addition to or a truncation of the ones
      in the indent above.
    * Parens also start lists, though a leading paren on a line does not
      suppress the creation of a list that would be started there due solely to
      whitespace. In other words, in "foo\n(bar)", "(bar)" parses as [[bar]],
      with the extra set of brackets provided by whitespace.
    * Indentation is ignored inside parens so you can use whitespace for human
      comprehension in non-machine-readable ways.

    """
    old_indent = None
    # A stack of lengths of indents of indentation-based lists that enclose this
    # one. There is an implicit top-level list enclosing the whole program. This
    # is at indent level 0.
    at = []
    # How many paren pairs we're inside:
    enclosing_parens = 0

    for match in token_pattern.finditer(text):
        type = match.lastgroup
        if type == 'dent':
            if enclosing_parens <= 0:  # Ignore indentation inside parens.
                new_indent = match.group('dent')
                if not at:  # BOF
                    at.append(0)
                    yield OPEN
                    yield OPEN
                elif new_indent == old_indent:  # same dent
                    yield CLOSE
                    # Open the new (sibling) list we're about
                    # to start making:
                    yield OPEN
                elif new_indent.startswith(old_indent):  # indent
                    at.append(len(new_indent))
                    # Open the first line of the block:
                    yield OPEN
                elif old_indent.startswith(new_indent):  # outdent
                    assert len(at) >= 2, "How can there be no encloser if we're outdenting?"
                    # You get one just for ending the line: this ends the
                    # current line's list.
                    yield CLOSE
                    if len(new_indent) <= at[-2]:  # full outdent  # TODO: Don't just measure and keep track of lengths of indents, or we won't be able to support mixed tabs and spaces. Or will we? Maybe it just works, since indenting always adds length and dedenting always subtracts it.
                        # Then you get another for each level you outdent:
                        while len(at) >= 2 and len(new_indent) <= at[-2]:
                            yield CLOSE
                            at.pop()
                        # Now we're going to start a new line, because otherwise
                        # this would be EOF and be taken care of down at the
                        # bottom of this proc.
                        yield OPEN
                    else:  # partial outdent
                        # We outdented from the previous line but not out to the
                        # level of the previous indent.

                        # Pop the indentation into the block we just closed:
                        at.pop()
                else:
                    raise LexError("Indentation was not consistent. The whitespace characters that make up each indent must be either an addition to or a truncation of the ones in the indent above. You can't just swap out tabs for spaces suddenly.")

                old_indent = new_indent

        elif type == 'paren':
            enclosing_parens += 1
            yield '('
        elif type == 'end_paren':
            if enclosing_parens <= 0:
                # We have to keep track of enclosing_parens anyway, so we might
                # as well raise this now rather than later, in the parser:
                raise LexError("You closed a parenthesis that wasn't open.")
            enclosing_parens -= 1
            yield ')'
        elif type == 'int':
            yield int(match.group())
        elif type == 'word':
            yield match.group()
        elif type == 'unmatched':
            raise LexError('Unrecognized token: "%s".' % match.group())

    did_any = False
    for indent in at:
        did_any = True
        yield CLOSE
    if did_any:
        yield CLOSE
    


def _parse_list(token_iter, return_at):
    """Start parsing the token stream at a list OPEN, either OPEN or '('.
    Parse until we reach the matching CLOSE, then return the parsed list plus a
    bool representing whether we collapsed the list from a 1-list to an atom
    (and thus it shouldn't be collapsed further)."""
    ret = []
    wrong_closer = ')' if return_at is CLOSE else CLOSE
    # Whether we already collapsed the single list inside ``ret`` to an atom:
    collapsed = False
    for token in token_iter:
        if token in (OPEN, '('):
            awaited_closer = CLOSE if token is OPEN else ')'
            l, collapsed = _parse_list(token_iter, awaited_closer)
            ret.append(l)
        elif token == return_at:
            # A single atom on a line is just the atom, not a 1-list of it:
            if len(ret) == 1 and not isinstance(ret[0], list) and return_at is CLOSE and not collapsed:
                # This is another way of saying we saw the token sequence
                # OPEN, atom, CLOSE.
                return ret[0], True
            return ret, False
        elif token == wrong_closer:
            # Superfluous end parentheses (that is, missing dedents) are caught
            # earlier, in the lexer.
            raise LexError("You're missing an end parenthesis.")
        else:
            ret.append(token)
    return ret, False


def parse(tokens):
    """Turn the token stream from the lexer into a parse tree.

    parse() won't work unless the stream starts with an OPEN and ends with a
    CLOSE.

    expr = atom | list
    atom = int | word
    list = (OPEN expr* CLOSE) | ('(' expr* ')')

    """
    token_iter = iter(tokens)

    # Keep _parse_list() from adding an additional nested list inside the one it
    # implicitly makes. It'll still happily match and consume the ending CLOSE.
    assert next(token_iter) is OPEN

    l, collapsed = _parse_list(token_iter, CLOSE)
    return l
    # TODO: Throw a fit if there are leftover tokens, meaning we prematurely closed all enclosers.
