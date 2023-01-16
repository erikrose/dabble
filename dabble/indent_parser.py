import re

from .exceptions import LexError


token_pattern = re.compile(
    # A line that's just whitespace and/or comment:
    r'(?P<skipped_line>^[ \t]*(?:#.*|)$)|'
    r'(?P<dent>^[ \t]*)|'
    r'(?P<horizontal_whitespace>[ \t]+)|'
    r'(?P<word>[-a-zA-Z+*/><=]+)|'
    r'(?P<int>(?:0|[1-9]([0-9])*))|'
    r'(?P<unmatched>.)',
    flags=re.M)


class TokenConst(object):
    """A way of expressing singleton tokens that pretty-prints nicely for
    tests"""

    def __init__(self, identity):
        self.identity = identity
    
    def __repr__(self):
        return self.identity


OPENER = TokenConst('OPENER')
CLOSER = TokenConst('CLOSER')


def lex(text):
    """Break down a string into an iterable of tokens based on indentation in a
    scheme akin to the I-expressions presented in SRFI 49.

    * Indenting starts a new list.
    * The list continues until indentation goes back to the pre-indented level.
    * Later?: One atom on a line is just an atom, not a 1-list. Yes: this will
      keep us from having to overnotate in the branches of ifs, which are
      common. And it will make our unary functions look like OCaml's--``foo
      ()``--which have proven tolerable. We don't want to do exotic things like
      make exceptions based on type (the expression is its own value if not a
      function, a function call if a function), because then you can't write the
      identity function and pass it a function. Finally, and most persuasively,
      this makes all function calls look alike: ``foo 1 2 3``, ``foo ()``.
    * Both tabs and spaces are considered indentation.
    * Inconsistent indentation is an error. The whitespace characters that make
      up each indent must be either an addition to or a truncation of the ones
      in the indent above.
    * Later: Indentation is ignored inside parens so you can use whitespace for
      human comprehension in non-machine-readable ways.

    The caller should create the top-level list all the yielded tokens go into.

    """
    old_indent = ''
    encloser_starts = []  # a stack of lengths of indents of lists that enclose this one
    ever_opened_anything = False

    for match in token_pattern.finditer(text):
        type = match.lastgroup
        if type == 'dent':
            new_indent = match.group('dent')
            if new_indent == old_indent:
                if ever_opened_anything:
                    yield CLOSER
            elif new_indent.startswith(old_indent):  # indent
                encloser_starts.append(len(old_indent))
            elif old_indent.startswith(new_indent):  # outdent
                # You get one just for ending the line: this ends the current
                # line's list.
                yield CLOSER
                # Then you get another for each level you outdent:
                while (encloser_starts and
                       encloser_starts[-1] >= len(new_indent)):
                    encloser_starts.pop()
                    yield CLOSER
            else:
                raise LexError("Indentation was not consistent. The whitespace characters that make up each indent must be either an addition to or a truncation of the ones in the indent above. You can't just swap out tabs for spaces suddenly.")

            # Open the new (child, sibling, or outdented) list we're about to
            # start making:
            yield OPENER
            ever_opened_anything = True
            old_indent = new_indent
        elif type == 'unmatched':
            raise LexError('Unrecognized token: "%s".' % match.group())
        elif type == 'int':
            yield int(match.group())
        elif type == 'word':
            yield match.group()

    for _ in encloser_starts:
        yield CLOSER
    if ever_opened_anything:
        yield CLOSER


def _parse_core(token_iter):
    ret = []
    for token in token_iter:
        if token is OPENER:
            ret.append(_parse_core(token_iter))
        elif token is CLOSER:
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
    return _parse_core(iter(tokens))
