from __future__ import annotations

import math

from evolution_strategy import EvolutionStrategy, objective


def test_objective_has_zero_minimum_for_printed_formula():
    assert objective([0.0, 0.0, 0.0]) == 0.0
    assert objective([1.0, 1.0]) == 15.0


def test_mutation_respects_bounds():
    es = EvolutionStrategy(3, seed=4)
    parent = es.make_individual()
    child = es.mutate(parent)
    assert all(es.lower <= value <= es.upper for value in child.x)
    assert math.isfinite(child.value)


def test_es_improves_initial_best():
    es = EvolutionStrategy(2, population_size=10, max_generations=30, seed=4)
    result = es.run()
    assert result.history[-1]["best_value"] <= result.history[0]["best_value"]
    assert result.best.value >= 0.0

