import numpy as np

from лр2.variant4_ga import (
    DEFAULT_BOUNDS,
    blx_alpha_crossover,
    moved_axis_parallel_hyperellipsoid,
    mutate,
    run_ga,
)


def test_variant4_has_declared_global_minimum_at_shifted_point():
    assert moved_axis_parallel_hyperellipsoid([5.0, 10.0, 15.0]) == 0.0
    assert moved_axis_parallel_hyperellipsoid([0.0, 0.0, 0.0]) > 0.0


def test_crossover_and_mutation_keep_genes_inside_bounds():
    rng = np.random.default_rng(7)
    p1 = np.array([-100.0, 0.0, 30.0])
    p2 = np.array([100.0, 50.0, -10.0])
    child = blx_alpha_crossover(p1, p2, rng, alpha=0.5, bounds=DEFAULT_BOUNDS)
    mutated = mutate(child, rng, mutation_probability=1.0, bounds=DEFAULT_BOUNDS)

    assert np.all(mutated >= DEFAULT_BOUNDS[0])
    assert np.all(mutated <= DEFAULT_BOUNDS[1])


def test_ga_is_reproducible_and_reaches_the_known_minimum_neighborhood():
    first = run_ga(n=2, population_size=80, seed=123, max_generations=500)
    second = run_ga(n=2, population_size=80, seed=123, max_generations=500)

    assert np.allclose(first.best_solution, second.best_solution)
    assert first.best_value == second.best_value
    assert first.best_value < 1.0
    assert np.allclose(first.best_solution, [5.0, 10.0], atol=0.2)
