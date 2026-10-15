from __future__ import annotations

import math

from gp_symbolic_regression import GeneticProgramming, Node, evaluate, expression, make_training_data, target_function


def test_target_formula_value():
    assert math.isclose(target_function(0.5), 0.140625, rel_tol=1e-12)


def test_safe_operations_are_finite():
    tree = Node("/", [Node("const", [], 1), Node("-", [Node("x", []), Node("x", [])])])
    assert math.isfinite(evaluate(tree, 0.25))


def test_tree_gp_reduces_error():
    x_values, y_values = make_training_data()
    gp = GeneticProgramming(x_values, y_values, population_size=100, generations=20, max_depth=6, seed=4)
    best, mse = gp.run()
    assert len(gp.history) == 21
    assert mse <= gp.history[0]["mse"]
    assert best.size() > 0
    assert expression(best)

