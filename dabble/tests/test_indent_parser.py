"""Tests for the indentation-based parser"""

from pytest import raises, skip

from dabble.indent_parser import lex, LexError, parse, OPENER, CLOSER


def lexed(text):
    return list(lex(text))


def test_comments_at_end_ignored():
    """We shouldn't have any hanging third opener at the end due to the trailing
    comment or newline."""
    text = """some dent
same dent
# Comment
"""
    assert lexed(text) == [
        OPENER,
            OPENER, 'some', 'dent', CLOSER,
            OPENER, 'same', 'dent', CLOSER,
        CLOSER]


def test_outdent_closer_count():
    """Make sure we're not off by one in outdent handler: we must yield the
    right number of closers after c. Multiple chars per indent level hide a
    multitude of off-by-one sins."""
    text = """a
 b
  c
d"""
    assert lexed(text) == [
        OPENER,
            OPENER, 'a',
                OPENER, OPENER, 'b',
                    OPENER, OPENER, 'c', CLOSER, CLOSER,
                CLOSER, CLOSER,
            CLOSER,
            OPENER, 'd', CLOSER,
        CLOSER]


def test_close_indents_at_eof():
    """Make sure we close all open indents at the EOF."""
    text = """a
 b
  c
   d"""
    assert lexed(text) == [
        OPENER,
        OPENER, 'a',
            OPENER, OPENER, 'b',
                OPENER, OPENER, 'c',
                    OPENER, OPENER, 'd', CLOSER, CLOSER,
                CLOSER, CLOSER,
            CLOSER, CLOSER,
        CLOSER,
        CLOSER]


def test_empty_text():
    """Make sure we do something reasonable on an empty file."""
    assert lexed('') == []


def test_everything_indented():
    """Make sure we allow things to just plain start indented. It's not vital,
    but it's nice for pasting into a REPL."""
    skip("We don't support this yet.")
    text = """ a
 b"""
    assert lexed(text) == [OPENER, 'a', CLOSER,
                           OPENER, 'b', CLOSER]


def test_lex_basics():
    """Make sure some basic contruct lex (or properly fail to)."""
    assert lexed('word***') == [OPENER, OPENER, 'word***', CLOSER, CLOSER]
    assert lexed('(8 9 abc+)') == [OPENER, OPENER, '(', 8, 9, 'abc+', ')', CLOSER, CLOSER]
    assert lexed('(1 2 (3 4))') == [OPENER, OPENER, '(', 1, 2, '(', 3, 4, ')', ')', CLOSER, CLOSER]
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
    assert parsed(text) == [['a', [['b', 0]]]]


def parsed(text):
    """Lex and parse one or more well-formed lines of code."""
    return parse(lex(text))


def test_parse_single_line():
    assert parse([OPENER, OPENER, 4, 5, CLOSER, CLOSER]) == [[4, 5]]


def test_parse_indented():
    text = """a
 b
  c 0
d"""
    assert lexed(text) == [
        OPENER,
            OPENER,
                'a',
                OPENER,
                    OPENER, 'b',
                        OPENER,
                            OPENER, 'c', 0, CLOSER,
                        CLOSER,
                    CLOSER,
                CLOSER,
            CLOSER,
            OPENER, 'd', CLOSER,  # This one will be collapsed from a 1-list to an atom.
        CLOSER
    ]
    assert parsed(text) == [['a', [['b', [['c', 0]]]]], 'd']


def test_single_atom_is_not_list():
    """A single atom on a line should be just the atom, not a 1-list."""
    # The list here is the all-containing list for the whole program:
    assert parsed('2') == [2]
    text = """
if smoo
    0
    1"""
    assert lexed(text) == [
        OPENER,
            OPENER, 'if', 'smoo',
                OPENER,
                    OPENER, 0, CLOSER,
                    OPENER, 1, CLOSER,
                CLOSER,
            CLOSER,
        CLOSER,
    ]
    assert parsed(text) == [['if', 'smoo', [0, 1]]]


def test_parens():
    assert parsed('1 (2 3 4) 5') == [[1, [2, 3, 4], 5]]
    assert parsed("""
1
    2 (3 4 5)""") == [[1, [[2, [3, 4, 5]]]]]


def test_single_atom_in_parens_is_a_list():
    """When a single atom is on a line by itself, it should be just the atom,
    but when a single atom is in parens by itself, it should be a 1-list."""
    text = """
fun (x)
    2"""
    # The brackets around the 2 are for the block. The ones for the line that
    # would make it a 1-list are gone.
    assert parsed(text) == [['fun', ['x'], [2]]]


def test_indentation_ignored_inside_parens():
    """Indentation inside parentheses shouldn't count for anything."""
    assert parsed("""
1
  2 (3
4
  5 6
7) 8""") == [[1, [[2, [3, 4, 5, 6, 7], 8]]]]


def test_partial_outdent():
    """Make sure we don't consider it an outdent until we outdent all the way to
    the enclosing indent level."""
    assert lexed("""
if foo
    1
  else
    0""") == [
    OPENER,
        OPENER,
            'if', 'foo',
                OPENER, OPENER, 1, CLOSER, CLOSER,
            'else',
                OPENER, OPENER, 0, CLOSER, CLOSER,
        CLOSER,
    CLOSER]
# I don't think an indent after a partial outdent is worth an indent.


def test_impartial_outdent():
    """Contrast with test_partial_outdent to learn in what situations closer behavior should be different."""
    assert lexed("""
if foo
    1
    0""") == [OPENER,
              OPENER, 'if', 'foo', OPENER,
              OPENER, 1, CLOSER,
              OPENER, 0, CLOSER,
              CLOSER, CLOSER,
              CLOSER]


def test_ending_at_partial_outdent():
    assert lexed("""
if foo
    1
  else""") == [
    OPENER,
        OPENER,
            'if', 'foo',
                OPENER, OPENER, 1, CLOSER, CLOSER,
            'else',
        CLOSER,
    CLOSER]


def test_one_liner():
    """Make sure we emit a trailing CLOSER for one-liners."""
    assert lexed("""foo""") == [OPENER, OPENER, 'foo', CLOSER, CLOSER]


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
