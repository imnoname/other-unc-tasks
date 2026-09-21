"""Вариант 20, часть 1: простейшая вариационная задача."""

from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class VariationalResult:
    """Символьный результат решения вариационной задачи."""

    x: sp.Symbol
    y: sp.Expr
    lagrangian: sp.Expr
    euler_lagrange: sp.Expr
    extremal: sp.Expr
    functional_value: sp.Expr


def solve_variational_problem() -> VariationalResult:
    """Решает задачу из варианта 20 средствами SymPy."""

    x = sp.symbols("x", real=True)
    y = sp.Function("y")(x)
    y_prime = sp.diff(y, x)

    lagrangian = x * y * y_prime - 2 * y_prime**2
    d_lagrangian_d_y = sp.diff(lagrangian, y)
    d_lagrangian_d_y_prime = sp.diff(lagrangian, y_prime)
    euler_lagrange = sp.simplify(
        d_lagrangian_d_y - sp.diff(d_lagrangian_d_y_prime, x)
    )

    general_solution = sp.dsolve(sp.Eq(euler_lagrange, 0), y).rhs
    constants = sorted(
        general_solution.free_symbols - {x}, key=lambda symbol: symbol.name
    )
    boundary_equations = [
        sp.Eq(general_solution.subs(x, 0), 1),
        sp.Eq(general_solution.subs(x, 1), sp.cosh(sp.Rational(1, 2))),
    ]
    constants_values = sp.solve(boundary_equations, constants, dict=True)[0]
    extremal = sp.simplify(
        general_solution.subs(constants_values).rewrite(sp.exp)
    ).rewrite(sp.cosh)
    extremal = sp.simplify(extremal)

    integrand_on_extremal = lagrangian.subs(
        {
            y: extremal,
            y_prime: sp.diff(extremal, x),
        }
    )
    functional_value = sp.simplify(
        sp.integrate(integrand_on_extremal, (x, 0, 1))
    )

    return VariationalResult(
        x=x,
        y=y,
        lagrangian=lagrangian,
        euler_lagrange=euler_lagrange,
        extremal=extremal,
        functional_value=functional_value,
    )


def main() -> None:
    result = solve_variational_problem()

    print("Вариант 20. Вариационная задача")
    print("Функционал:", result.lagrangian)
    print("Уравнение Эйлера–Лагранжа:", sp.Eq(result.euler_lagrange, 0))
    print("Экстремаль:", result.extremal)
    print("Значение функционала:", result.functional_value)
    print("Приближённое значение:", sp.N(result.functional_value, 10))


if __name__ == "__main__":
    main()
