from pytest import skip

from dabble.environment import Environment
from dabble.interpreter import eval, pervasives, run

from .testing import eval_with_new_env


def test_numbers_evaluate_to_themselves():
    assert run('1') == 1


def test_string_literals_evaluate_to_themselves():
    skip("We don't support strings yet.")
    assert run('"hello"') == 'hello'


def test_addition():
    assert run('+ 1 2') == 3


def test_expressions_as_addends():
    assert run('+ (+ 3 2) 5') == 10


def test_var_declaration_and_lookup():
    env = Environment(parent=pervasives)
    assert eval(['set', 'x', 10], env) == 10
    assert eval('x', env) == 10


def test_if_and_greater_than():
    assert eval_with_new_env(
        ['begin',
            ['set', 'x', 10],
            ['set', 'y', 0],
            ['if', ['>', 'x', 10],
                ['set', 'y', 20],
                ['set', 'y', 30],
            ],
            'y'
        ]
    ) == 30


def test_while():
    assert eval_with_new_env(
        ['begin',
            ['set', 'counter', 0],
            ['while', ['<', 'counter', 10],
                ['set', 'counter', ['+', 'counter', 1]]
            ],
            'counter'
        ]
    ) == 10


def test_begin():
    """Make sure `begin` executes things in sequence and the value is the last
    expression."""
    assert eval_with_new_env(
            ['begin',
                ['set', 'x', 10],
                ['set', 'y', 20],
                ['+', ['*', 'x', 'y'], 30]
            ]
    ) == 230
