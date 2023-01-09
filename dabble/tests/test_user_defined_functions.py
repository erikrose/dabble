from dabble.interpreter import run


def test_first_class_lambda():
    assert run("""
        (var on-click
            (fun (callback)
                (begin
                    (var x 10)
                    (var y 20)
                    (callback (+ x y))
                )
            )
        )

        (on-click (fun (data) (* data 10)))
    """) == 300


def test_function_definition_and_evaluation():
    assert run("""
        (var square
            (fun (x)
                (* x x)
            )
        )

        (square 2)
    """) == 4


def test_function_containing_block():
    """Begin creates yet another new scope. Make sure that doesn't cause any
    problems."""
    assert run("""
        (var calc (fun (x y)
                      (begin
                          (var z 30)
                          (+ (* x y) z))))

        (calc 10 20)
    """) == 230


def test_closures_and_first_class_functions():
    assert run("""
        (var make_adder
            (fun (how_much)
                (var adder
                    (fun (addend)
                        (+ addend how_much)))))

        (var my_adder (make_adder 100))
        (my_adder 50)
    """) == 150


def test_recursion():
    assert run("""
        (var factorial 
            (fun (x)
                (if (== x 1)
                    1
                    (* x (factorial (- x 1))))))

        (factorial 5)
    """) == 120


def test_functions_make_new_scopes():
    """Make sure functions introduce their own new scopes.

    A var declared in one shouldn't leak to the outside.

    """
    assert run("""
        (var x 8)
        (var frob
            (fun ()
                (var x 9)))
        (frob)
        x
    """) == 8


def test_nested_functions_make_new_scopes():
    """Make sure inner functions' vars don't leak into outers' scopes."""
    assert run("""
        (var frob
            (fun ()
                (begin
                    (var x 1)
                    ((fun ()
                        (var x 2)))
                    x)))

        (frob)
    """) == 1
