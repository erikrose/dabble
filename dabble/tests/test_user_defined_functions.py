from dabble.interpreter import run


def test_first_class_lambda():
    assert run("""
set on-click
    fun (callback)
        begin
            set x 10
            set y 20
            callback (+ x y)

on-click
    fun (data)
        * data 10
    """) == 300


def test_function_definition_and_evaluation():
    assert run("""
set square
    fun (x)
        * x x

square 2
    """) == 4


def test_closures_and_first_class_functions():
    assert run("""
set make-adder
    fun (how-much)
        fun (addend)
            + addend how-much

set my-adder (make-adder 100)
my-adder 50
    """) == 150


def test_recursion():
    assert run("""
set factorial 
    fun (x)
        if (== x 1)
            1
            * x (factorial (- x 1))

factorial 5
    """) == 120


def test_functions_make_new_scopes():
    """Make sure functions introduce their own new scopes.

    A var set in one shouldn't leak to global namespace.

    """
    assert run("""
set x 8
set frob
    fun ()
        set x 9
(frob)
x
    """) == 8


def test_nested_functions_make_new_scopes():
    """Make sure inner functions' vars don't leak into outers' scopes."""
    assert run("""
set frob
    fun ()
        begin
            set x 1
            set smoo
                fun ()
                    set x 2
            (smoo)
            x

(frob)
    """) == 1
