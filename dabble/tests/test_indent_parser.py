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
        OPENER, 'some', 'dent', CLOSER,
        OPENER, 'same', 'dent', CLOSER]


def test_outdent_closer_count():
    """Make sure we're not off by one in outdent handler: we must yield the
    right number of closers after c. Multiple chars per indent level hide a
    multitude of off-by-one sins."""
    text = """a
 b
  c
d"""
    assert lexed(text) == [
        OPENER, 'a',
            OPENER, 'b',
                OPENER, 'c', CLOSER,
            CLOSER,
        CLOSER,
        OPENER, 'd', CLOSER]


def test_close_indents_at_eof():
    """Make sure we close all open indents at the EOF."""
    text = """a
 b
  c
   d"""
    assert lexed(text) == [
        OPENER, 'a',
            OPENER, 'b',
                OPENER, 'c',
                    OPENER, 'd', CLOSER,
                CLOSER,
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


def test_basics():
    #assert parsed('"hi"') == '"hi"'
    assert parsed('word***') == ['word***']
    assert parsed('(8 9 abc+)') == [[8, 9, 'abc+']]
    assert parsed('(1 2 (3 4))') == [[1, 2, [3, 4]]]
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
    return parse(lex(text))


def test_parse_single_line():
    assert parse([OPENER, 4, 5, CLOSER]) == [[4, 5]]


def test_parse_indented():
    text = """a
 b
  c 0
d"""
    assert parsed(text) == [['a', ['b', ['c', 0]]], 'd']


def test_single_atom_is_not_list():
    """A single atom on a list should be just the atom, not a 1-list."""
    assert parsed('2') == [2]
    assert parsed("""
if smoo
    0
    1""") == [['if', 'smoo', 0, 1]]


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
    assert parsed(text) == [['fun', ['x'], 2]]
