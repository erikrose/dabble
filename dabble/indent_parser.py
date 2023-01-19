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


# OPENER and CLOSER represent the start and end of a whitespace-delimited list.
# They do not correspond directly to indents and outdents.
OPENER = TokenConst('OPENER')
CLOSER = TokenConst('CLOSER')


def lex(text):
    """Break down a string into an iterable of tokens based on indentation in a
    scheme akin to the I-expressions presented in SRFI 49.

    * Indenting starts a new list.
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
    * Later: Indentation is ignored inside parens so you can use whitespace for
      human comprehension in non-machine-readable ways.

    The caller should create the top-level list all the yielded tokens go into.

    """
    old_indent = ''
    # A stack of lengths of indents of indentation-based lists that enclose this
    # one:
    encloser_starts = []
    ever_opened_anything = False
    # How many paren pairs we're inside:
    enclosing_parens = 0

    for match in token_pattern.finditer(text):
        type = match.lastgroup
        if type == 'dent':
            if not enclosing_parens:  # Ignore indentation inside parens.
                new_indent = match.group('dent')
                if new_indent == old_indent:
                    if ever_opened_anything:
                        yield CLOSER
                elif new_indent.startswith(old_indent):  # indent
                    encloser_starts.append(len(old_indent))
                elif old_indent.startswith(new_indent):  # outdent
                    # You get one just for ending the line: this ends the
                    # current line's list.
                    yield CLOSER
                    # Then you get another for each level you outdent:
                    while (encloser_starts and
                           encloser_starts[-1] >= len(new_indent)):
                        encloser_starts.pop()
                        yield CLOSER
                else:
                    raise LexError("Indentation was not consistent. The whitespace characters that make up each indent must be either an addition to or a truncation of the ones in the indent above. You can't just swap out tabs for spaces suddenly.")

                # Open the new (child, sibling, or outdented) list we're about
                # to start making:
                yield OPENER
                ever_opened_anything = True
                old_indent = new_indent
        elif type == 'paren':
            enclosing_parens += 1
            yield '('
        elif type == 'end_paren':
            if enclosing_parens <= 0:
                raise LexError("You closed a parenthesis that wasn't open.")
            enclosing_parens -= 1
            yield ')'
        elif type == 'int':
            yield int(match.group())
        elif type == 'word':
            yield match.group()
        elif type == 'unmatched':
            raise LexError('Unrecognized token: "%s".' % match.group())

    for _ in encloser_starts:
        yield CLOSER
    if ever_opened_anything:
        yield CLOSER


def _parse_core(token_iter, closer_we_are_waiting_for):
    ret = []
    for token in token_iter:
        if token in (OPENER, '('):
            ret.append(_parse_core(token_iter, CLOSER if token is OPENER else ')'))
        elif token is closer_we_are_waiting_for:
            # A single atom on a line is just the atom, not a 1-list:
            if len(ret) == 1 and closer_we_are_waiting_for is CLOSER:
                # This is another way of saying we saw the token sequence
                # OPENER, atom, CLOSER.
                return ret[0]
            return ret
        else:
            ret.append(token)
    return ret


def parse(tokens):
    """Turn the token stream from the lexer into a parse tree.

    expr = atom | list
    atom = int | word
    list = OPENER expr* CLOSER

    """
    return _parse_core(iter(tokens), CLOSER)
