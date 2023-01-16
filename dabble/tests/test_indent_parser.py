"""Tests for the indentation-based parser"""

from pytest import skip

from dabble.indent_parser import lex, parse, OPENER, CLOSER
from dabble.parser import parse as parse_parenthesized


def test_basics():
    """Make sure lists and single-atoms-on-a-line parse."""
    skip("Single atoms on a line are currently construed as 1-lists. Not sure if we're going to change that. Also, parser atop indentation lexer isn't yet implemented.")
    indented = """set x to 8
set frob to
    function emptyList
        set x to 9
frob emptyList
x"""
    parenthesized = """(
(set x 8)
(set frob
    (fun ()
        (set x 9)))
(frob ())
x
)"""
    assert parse(indented) == parse_parenthesized(parenthesized)


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
    assert parsed(text) == [['a', ['b', ['c', 0]]], ['d']]
