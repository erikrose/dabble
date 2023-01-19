from operator import lt, gt, le, ge, eq, add, mul, floordiv
import re
from sys import argv

from .environment import Environment
from .indent_parser import lex, parse


pervasives = Environment({
    'true': True,
    'false': False,

    '+': add,
    '*': mul,
    '-': lambda op1, op2=None: -op1 if op2 is None else (op1 - op2),
    '/': floordiv,
    '>': gt,
    '<': lt,
    '>=': ge,
    '<=': le,
    '==': eq,
})


def eval(exp, env):
    """Evaluate an expression.

    :arg exp: The expression as an s-expression stored as a Python list
    :arg env Environment: The scope to look up or create vars in

    """
    # Numeric literals:
    if is_number(exp):
        return exp

    # String literals:
    if is_string(exp):
        return exp[1:-1]

    # Var lookup:
    if is_variable_name(exp):
        return env.look_up(exp)

    verb = exp[0]

    # Sequences. These don't introduce a new scope. Their value is that of their
    # last expression.
    if verb == 'begin':
        return _eval_block(exp, env)

    # Assignment:
    if verb == 'set':
        _, ref, value = exp  # can be a var name of a ref, like to a class instance
        return env.assign(ref, eval(value, env))

    # If:
    if verb == 'if':
        _, condition, consequent, alternate = exp
        if eval(condition, env):
            return eval(consequent, env)
        else:
            return eval(alternate, env)

    # While:
    if verb == 'while':
        _, condition, body = exp
        result = None
        # We require condition to be true, not just truthy:
        while eval(condition, env) == True:
            result = eval(body, env)
        return result

    # Could add lists:
    # (var values (list 42 "Hello" foo))  # Add a native "list" function that sucks up its args and socks them into an array behind the scenes. If you just said (1 2 3), it would try calling 1 as a function.
    # (. values 1)  # Then you can reuse `.` to get them out, or make up a new method.

    # User-defined functions:
    if verb == 'fun':
        _, params, body = exp
        return Function(
            params,
            # Notice we don't evaluate the body yet:
            body,
            # All functions are closures in Dabble, so we capture the env:
            env)

    # Function calls:
    if isinstance(exp, list):
        fn = eval(verb, env)
        args = [eval(e, env) for e in exp[1:]]
        if callable(fn):  # Native functions 
            return fn(*args)
        elif isinstance(fn, Function):
            # Make an empty env with nothing in it but bound param names.
            # (This is called the "activation environment".) It points to
            # the closed-over env as its parent.
            params_env = Environment(vars=dict(zip(fn.params, args)),
                                     parent=fn.env)
            return eval(fn.body, params_env)

    raise Exception(f'Unimplemented: {exp}')


def run(program, env=None):
    """Evaluate a string containing a sequence of s-exprs as a Dabble
    program."""
    if env is None:
        env = Environment(parent=pervasives)
    parsed = parse(lex(program))
    return _eval_block(['dummy', *parsed], env)


def _eval_block(block, env):
    """Evaluate each expression of a `begin` block in an environment. Value is
    the value of the last expression."""
    result = None
    expressions = block[1:]
    for exp in expressions:
        result = eval(exp, env)
    return result


def is_number(exp):
    return isinstance(exp, int)


def is_string(exp):
    """Return whether the expression is a Dabble string literal."""
    return isinstance(exp, str) and len(exp) >= 2 and exp[0] == '"' and exp[-1] == '"'


def is_variable_name(exp):
    return isinstance(exp, str) and re.fullmatch(r'^[+\-*/<>=a-zA-Z0-9_]+$', exp)


class Function:
    """A user-defined function"""

    def __init__(self, params, body, env):
        """
        :arg params: A list of the function's param names
        :arg body: The unevaluated body of the function
        :arg env: The closed-over env of the function
        """
        self.params = params
        self.body = body
        self.env = env

    def call(self, *args):
        # Make an empty env with nothing in it but bound param names. (This is
        # called the "activation environment".) It points to the closed-over env
        # as its parent.
        params_env = Environment(vars=dict(zip(self.params, args)),
                                 parent=self.env)
        return eval(self.body, params_env)

    def __str__(self):
        return f'<Function ({self.params})>'
