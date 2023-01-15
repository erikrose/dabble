import re

from .exceptions import LexError


token_pattern = re.compile(
    # A line that's just whitespace and/or comment:
    r'(?P<skipped_line>^[ \t]*(?:#.*|)$)|'
    r'(?P<dent>^[ \t]*)|'
    r'(?P<horizontal_whitespace>[ \t]+)|'
    r'(?P<word>[-a-zA-Z]+)|'
    r'(?P<int>1-9(0-9)*)|'
    r'(?P<unmatched>.)',
    flags=re.M)


class TokenConst(object):
    """A way of expressing valueless tokens that pretty-prints nicely for
    tests"""

    def __init__(self, identity):
        self.identity = identity
    
    def __repr__(self):
        return self.identity


OPENER = TokenConst('OPENER')
CLOSER = TokenConst('CLOSER')


def lex_indented(text):
    """Break down a string into an iterable of tokens based on indentation in a
    scheme akin to the I-expressions presented in SRFI 49.

    * Indenting starts a new list.
    * The list continues until indentation goes back to the pre-indented level.
    * Later?: One atom on a line is just an atom, not a 1-list.
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
                yield OPENER  # Factor this...
                ever_opened_anything = True  # ...and this up.
            elif new_indent.startswith(old_indent):  # indent
                # Open the nested list we're about to start making:
                yield OPENER
                ever_opened_anything = True
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
                # Then we start the new line's list:
                yield OPENER
            else:
                raise LexError("Indentation was not consistent. The whitespace characters that make up each indent must be either an addition to or a truncation of the ones in the indent above. You can't just swap out tabs for spaces suddenly.")
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
