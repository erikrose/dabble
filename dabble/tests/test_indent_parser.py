"""Tests for the indentation-based parser"""

from pytest import raises, skip

from dabble.indent_parser import lex, LexError, parse, OPEN, CLOSE


def lexed(text):
    return list(lex(text))


def test_comments_at_end_ignored():
    """We shouldn't have any hanging third OPEN at the end due to the trailing
    comment or newline."""
    text = """some dent
same dent
# Comment
"""
    assert lexed(text) == [
        OPEN,
            OPEN, 'some', 'dent', CLOSE,
            OPEN, 'same', 'dent', CLOSE,
        CLOSE]


def test_outdent_closer_count():
    """Make sure we're not off by one in outdent handler: we must yield the
    right number of closers after c. Multiple chars per indent level hide a
    multitude of off-by-one sins."""
    text = """a
 b
  c
d"""
    assert lexed(text) == [
        OPEN,
            OPEN, 'a',
                OPEN, 'b',
                    OPEN, 'c', CLOSE,
                CLOSE,
            CLOSE,
            OPEN, 'd', CLOSE,
        CLOSE]


def test_close_indents_at_eof():
    """Make sure we close all open indents at the EOF."""
    text = """a
 b
  c
   d"""
    assert lexed(text) == [
        OPEN,
        OPEN, 'a',
            OPEN, 'b',
                OPEN, 'c',
                    OPEN, 'd', CLOSE,
                CLOSE,
            CLOSE,
        CLOSE,
        CLOSE]


def test_empty_text():
    """Make sure we do something reasonable on an empty file."""
    assert lexed('') == []


def test_everything_indented():
    """Make sure we allow things to just plain start indented. It's not vital,
    but it's nice for pasting into a REPL."""
    skip("We don't support this yet.")
    text = """ a
 b"""
    assert lexed(text) == [OPEN, 'a', CLOSE,
                           OPEN, 'b', CLOSE]


def test_lex_basics():
    """Make sure some basic contruct lex (or properly fail to)."""
    assert lexed('word***') == [OPEN, OPEN, 'word***', CLOSE, CLOSE]
    assert lexed('(8 9 abc+)') == [OPEN, OPEN, '(', 8, 9, 'abc+', ')', CLOSE, CLOSE]
    assert lexed('(1 2 (3 4))') == [OPEN, OPEN, '(', 1, 2, '(', 3, 4, ')', ')', CLOSE, CLOSE]
    with raises(LexError):
        lexed(')')


def test_parse_basics():
    #assert parsed('"hi"') == '"hi"'  # strings not supported yet
    assert parsed('word***') == ['word***']
    assert parsed('(8 9 abc+)') == [[[8, 9, 'abc+']]]
    assert parsed('(1 2 (3 4))') == [[[1, 2, [3, 4]]]]
    with raises(LexError):
        parsed(')')


def test_unclosed_parens():
    with raises(LexError):
        parsed('(1 2')


def test_whitespace_only_lines_are_skipped():
    """Make sure lines consisting only of whitespace have no effect on the
    surrounding indentation."""
    text = """a

     b 0"""
    assert parsed(text) == [['a', ['b', 0]]]


def parsed(text):
    """Lex and parse one or more well-formed lines of code."""
    return parse(lex(text))


def test_parse_single_line():
    assert parse([OPEN, OPEN, 4, 5, CLOSE, CLOSE]) == [[4, 5]]


def test_parse_indented():
    text = """a
 b
  c 0
d"""
    assert lexed(text) == [
        OPEN,
            OPEN,
                'a',
                OPEN, 'b',
                    OPEN, 'c', 0, CLOSE,
                CLOSE,
            CLOSE,
            OPEN, 'd', CLOSE,  # This one will be collapsed from a 1-list to an atom.
        CLOSE
    ]
    assert parsed(text) == [['a', ['b', ['c', 0]]], 'd']


def test_single_atom_is_not_list():
    """A single atom on a line should be just the atom, not a 1-list."""
    # The list here is the all-containing list for the whole program:
    assert parsed('2') == [2]
    text = """
if smoo
    0
    1"""
    assert lexed(text) == [
        OPEN,
            OPEN, 'if', 'smoo',
                OPEN, 0, CLOSE,
                OPEN, 1, CLOSE,
            CLOSE,
        CLOSE,
    ]
    assert parsed(text) == [['if', 'smoo', 0, 1]]


def test_parens():
    assert parsed('1 (2 3 4) 5') == [[1, [2, 3, 4], 5]]
    assert parsed("""
1
    2 (3 4 5)""") == [[1, [2, [3, 4, 5]]]]


def test_single_atom_in_parens_is_a_list():
    """When a single atom is on a line by itself, it should be just the atom,
    but when a single atom is in parens by itself, it should be a 1-list."""
    text = """
fun (x)
    2"""
    # The brackets that would have made the 2 a 1-list are gone.
    assert parsed(text) == [['fun', ['x'], 2]]


def test_indentation_ignored_inside_parens():
    """Indentation inside parentheses shouldn't count for anything."""
    assert parsed("""
1
  2 (3
4
  5 6
7) 8""") == [[1, [2, [3, 4, 5, 6, 7], 8]]]


def test_partial_outdent():
    """Make sure we don't consider it an outdent until we outdent all the way to
    the enclosing indent level."""
    assert lexed("""
if foo
    1
  else
    0""") == [
    OPEN,
        OPEN,
            'if', 'foo',
                OPEN, 1, CLOSE,
            'else',
                OPEN, 0, CLOSE,
        CLOSE,
    CLOSE]
# I don't think an indent after a partial outdent is worth an indent.


def test_impartial_outdent():
    """Contrast with test_partial_outdent to learn in what situations CLOSE behavior should be different."""
    assert lexed("""
if foo
    1
    0""") == [OPEN,
              OPEN, 'if', 'foo',
              OPEN, 1, CLOSE,
              OPEN, 0, CLOSE,
              CLOSE,
              CLOSE]


def test_ending_at_partial_outdent():
    assert lexed("""
if foo
    1
  else""") == [
    OPEN, OPEN,
        'if', 'foo',
            OPEN, 1, CLOSE,
        'else',
    CLOSE, CLOSE]


def test_one_liner():
    """Make sure we emit a trailing CLOSE for one-liners."""
    assert lexed("""foo""") == [OPEN, OPEN, 'foo', CLOSE, CLOSE]


def test_1_lists():
    """Make sure we can represent a list of 1 element on a line by itself."""
    assert lexed("""(frob)""") == [OPEN, OPEN, '(', 'frob', ')', CLOSE, CLOSE]
    assert parsed("""(frob)""") == [  # BOF OPEN
        ['frob']
    ]  # EOF CLOSE
    # When this passes, take the workarounds out of
    # test_functions_make_new_scopes and test_nested_functions_make_new_scopes.


# if foo
#     1
#   else  # Is this an encloser_start we need to close eventually? Why or why not?
#     0
# 
# vs.
# 
# if foo
#     1
#   if bar  # partial outdent means a continuation of enclosing list. partial means not all the way to enclosing level.
#     2
# 
# if foo
#     1 2
#   if bar
#  if baz
#     2 3
# should mean [if foo [1 2] if bar if baz [2 3]]
# 
# if foo
#     1
#   else  # Is this an encloser_start we need to close eventually? Why or why not? Never. You need to close due to a thing being INDENTED, like the "if" that immediately follows. There is no indent here; it is solely and unambiguously a partial outdent.
#     if bar
#         3
#     0


# if foo
#     0
#   else
#     1
#   otherwise
#     2
# # means [if foo [0] else [1] otherwise [2]]
# 
# if foo
#     0
#   else
#     1
#  otherwise
#     2
# # means the same
# 
# if foo
#     0
#   else
#     1
#    otherwise
#     2
# # means the same


# Does…
#     if foo
#         0
#     [[if foo [[0]]]]  # with atoms as lists (as the lexer should render them), not mere atoms
# …need fewer closers than…
#     if foo
#         0
#       else
#         1
#     [[if foo [[0]] else [[1]]]]
# …? [No.] If so, why? Does it *get* fewer closers? [No.] That could crack this problem wide open.
