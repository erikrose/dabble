from .testing import eval_with_new_env


def test_blocks():
    assert eval_with_new_env(
            [
                'begin',
                ['var', 'x', 10],
                ['var', 'y', 20],
                ['+', ['*', 'x', 'y'], 30]
            ]
    ) == 230


def test_inner_blocks_dont_overwrite_outer_ones_vars():
    assert eval_with_new_env(
        [
            'begin',
            ['var', 'x', 10],
            ['begin',
                ['var', 'x', 20],
                'x'
            ],
            'x'
        ]
    ) == 10


def test_inner_blocks_can_see_outer_ones_vars():
    assert eval_with_new_env(
        [
            'begin',
            ['var', 'value', 10],
            ['var', 'result', 
                ['begin',
                ['var', 'x', ['+', 'value', 10]],
                'x'
                ]
            ],
            'result'
        ]
    ) == 20


def test_inner_blocks_can_write_to_closed_over_vars():
    assert eval_with_new_env(
        [
            'begin',
            ['var', 'data', 10],
            ['begin',
                ['set', 'data', 100]
            ],
            'data'
        ]
    ) == 100
