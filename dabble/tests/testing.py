from dabble.environment import Environment
from dabble.interpreter import eval, pervasives


def eval_with_new_env(exp):
    """Evaluate a single expression in a top-level evaluator with just
    pervasives."""
    return eval(exp, Environment(parent=pervasives))
