"""Вариант 20, часть 2: целочисленная задача раскроя фанеры."""

from dataclasses import dataclass
from math import ceil


REQUIREMENTS = (24, 31, 18)
PATTERN_1 = (2, 5, 2)
PATTERN_2 = (6, 4, 3)
WASTE_1 = 12
WASTE_2 = 16


@dataclass(frozen=True)
class CuttingSolution:
    """Оптимальный план раскроя и его характеристики."""

    x1: int
    x2: int
    produced: tuple[int, int, int]
    waste: int


def produced_parts(x1: int, x2: int) -> tuple[int, int, int]:
    """Возвращает количество заготовок каждого вида для плана (x1, x2)."""

    return tuple(
        x1 * part_1 + x2 * part_2
        for part_1, part_2 in zip(PATTERN_1, PATTERN_2)
    )


def is_feasible(x1: int, x2: int) -> bool:
    """Проверяет неотрицательность и выполнение всех потребностей."""

    if not isinstance(x1, int) or not isinstance(x2, int):
        return False
    if x1 < 0 or x2 < 0:
        return False

    return all(
        actual >= required
        for actual, required in zip(produced_parts(x1, x2), REQUIREMENTS)
    )


def _waste(x1: int, x2: int) -> int:
    return WASTE_1 * x1 + WASTE_2 * x2


def solve_cutting_problem() -> CuttingSolution:
    """Находит оптимальный целочисленный план полным перебором.

    Сначала строится допустимый план только каждым из двух способов.
    Его отходы дают верхнюю границу, после чего перебираются все планы,
    которые могут улучшить или повторить найденное значение.
    """

    one_pattern_1 = max(
        ceil(required / parts)
        for required, parts in zip(REQUIREMENTS, PATTERN_1)
    )
    one_pattern_2 = max(
        ceil(required / parts)
        for required, parts in zip(REQUIREMENTS, PATTERN_2)
    )
    candidates = [(one_pattern_1, 0), (0, one_pattern_2)]
    best_plan = min(candidates, key=lambda plan: (_waste(*plan), plan))

    upper_waste = _waste(*best_plan)
    max_x1 = upper_waste // WASTE_1
    max_x2 = upper_waste // WASTE_2

    feasible_plans = [
        (x1, x2)
        for x1 in range(max_x1 + 1)
        for x2 in range(max_x2 + 1)
        if is_feasible(x1, x2)
    ]
    best_plan = min(feasible_plans, key=lambda plan: (_waste(*plan), plan))
    x1, x2 = best_plan

    return CuttingSolution(
        x1=x1,
        x2=x2,
        produced=produced_parts(x1, x2),
        waste=_waste(x1, x2),
    )


def main() -> None:
    result = solve_cutting_problem()

    print("Вариант 20. Раскрой фанеры")
    print("Модель: минимизировать 12*x1 + 16*x2")
    print("Ограничения:")
    print("  2*x1 + 6*x2 >= 24")
    print("  5*x1 + 4*x2 >= 31")
    print("  2*x1 + 3*x2 >= 18")
    print("  x1, x2 — целые неотрицательные")
    print(f"Оптимальный план: x1 = {result.x1}, x2 = {result.x2}")
    print("Получено заготовок I, II, III:", result.produced)
    print("Минимальные отходы:", result.waste, "см^2")


if __name__ == "__main__":
    main()
