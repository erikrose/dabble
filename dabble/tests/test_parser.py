from pytest import raises

from dabble.parser import parse, ParseError


def test_everything():
    assert parse('8') == 8
    assert parse('"hi"') == '"hi"'
    assert parse('symbol***') == 'symbol***'
    assert parse('(8 9 "abc" q+)') == [8, 9, '"abc"', 'q+']
    assert parse('(1 2 (3 4))') == [1, 2, [3, 4]]
    with raises(ParseError):
        parse('(1 2')
    with raises(ParseError):
        parse(')')
    with raises(ParseError):  # More rotten stuff after end of expr
        parse('(1 2) three')
