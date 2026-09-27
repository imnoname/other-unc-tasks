from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import P04, SET7
from knapsack_ga import evaluate, exact_optimum, genetic_algorithm


def test_p04_data_and_exact_optimum():
    assert len(P04.weights) == 7
    optimum = exact_optimum(P04)
    assert optimum.chromosome == (1, 0, 0, 1, 0, 0, 0)
    assert optimum.weight == 50
    assert optimum.profit == 107


def test_set7_data_shape():
    assert len(SET7.weights) == 50
    assert len(SET7.profits) == 50
    assert SET7.capacity == 12828


def test_repair_returns_a_valid_solution():
    result = evaluate([1] * len(P04.weights), P04)
    assert result.weight <= P04.capacity
    assert len(result.chromosome) == len(P04.weights)
    assert all(gene in (0, 1) for gene in result.chromosome)


def test_ga_is_reproducible_and_reaches_p04_optimum():
    first = genetic_algorithm(P04, population_size=40, generations=120, seed=42)
    second = genetic_algorithm(P04, population_size=40, generations=120, seed=42)
    assert first.best == second.best
    assert first.best.profit == 107
    assert first.best.weight == 50
