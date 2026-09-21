import sympy as sp

from variant20_cutting import is_feasible, solve_cutting_problem
from variant20_variational import solve_variational_problem


def test_variational_solution_satisfies_euler_lagrange_and_boundary_conditions():
    result = solve_variational_problem()
    x = result.x

    assert sp.simplify(result.euler_lagrange) == 4 * sp.diff(result.y, x, 2) - result.y
    assert sp.simplify(result.extremal.subs(x, 0) - 1) == 0
    assert sp.simplify(result.extremal.subs(x, 1) - sp.cosh(sp.Rational(1, 2))) == 0


def test_variational_solution_returns_functional_value_on_extremal():
    result = solve_variational_problem()
    expected = sp.Rational(1, 4) + sp.cosh(1) / 4 - sp.sinh(1) / 2

    assert sp.simplify(result.functional_value - expected) == 0


def test_cutting_solution_is_feasible_and_minimal():
    result = solve_cutting_problem()

    assert (result.x1, result.x2) == (3, 4)
    assert result.produced == (30, 31, 18)
    assert result.waste == 100
    assert is_feasible(result.x1, result.x2)


def test_cutting_solution_has_no_better_integer_plan():
    result = solve_cutting_problem()

    for x1 in range(result.x1 + result.x2 + 1):
        for x2 in range(result.x1 + result.x2 + 1):
            if is_feasible(x1, x2):
                assert 12 * x1 + 16 * x2 >= result.waste
