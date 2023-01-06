from collections import namedtuple
import re


WS = r'(?P<WS>\s+)'
STRING = r'(?P<STRING>\"[^\"]*")'
NUMBER = r'(?P<NUMBER>\d+)'
SYMBOL = r'(?P<SYMBOL>[\w\-+*=<>/]+)'
LPAREN = r'(?P<LPAREN>\()'
RPAREN = r'(?P<RPAREN>\))'
GARBAGE = r'(?P<GARBAGE>[^ ]+)'  # Anything the other patterns didn't catch, all the way to a space, so we can complain about it


token_pattern = re.compile('|'.join((WS, STRING, NUMBER, SYMBOL, LPAREN, RPAREN, GARBAGE)))
Token = namedtuple('Token', ['type', 'value'])


class ParseError(Exception):
    pass


def parse(sexprs):
    """Return an AST of the s-expr syntax.

    expr = atom | list
    atom = number | string | symbol
    list = ( expr* )

    """
    def token_iter():
        matches = re.finditer(token_pattern, sexprs)
        for match in matches:
            t = Token(match.lastgroup, match.group(0))
            if t.type != 'WS':
                yield t

    def advance():
        """Move parser state along to the next token."""
        nonlocal current_token, next_token
        current_token, next_token = next_token, next(tokens, None)

    def accept(token_type):
        if next_token and next_token.type == token_type:
            advance()
            return True
        return False

    def expr():
        if accept('LPAREN'):
            return list_()
        elif accept('NUMBER'):
            return int(current_token.value)
        elif accept('STRING'):
            return current_token.value
        elif accept('SYMBOL'):
            return current_token.value
        else:
            got = next_token.type if next_token else 'EOF'
            raise ParseError(f'Expected list or atom but got {got}.')

    def list_():
        ret = []
        while True:
            if accept('RPAREN'):
                break
            else:
                ret.append(expr())
        return ret

    tokens = token_iter()
    current_token = next_token = None
    advance()
    ret = expr()
    if next_token is not None:
        raise ParseError(f'More stuff was found after end of expression: {next_token.value}.')
    return ret
