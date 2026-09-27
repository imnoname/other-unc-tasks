"""Real-coded genetic algorithm for laboratory work 2, variant 4."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Iterable

import numpy as np


DEFAULT_BOUNDS = (-20.0, 20.0)


def target_point(n: int) -> np.ndarray:
    """Return the analytical optimum x_i = 5*i for one-based i."""

    if n < 1:
        raise ValueError("n must be positive")
    return 5.0 * np.arange(1, n + 1, dtype=float)


def moved_axis_parallel_hyperellipsoid(x: Iterable[float]) -> float:
    """Evaluate the shifted, weighted hyperellipsoid from variant 4.

    The methodical table names the function as shifted and declares x_i = 5*i
    as its global minimizer. The mathematically consistent form is
    sum(5*i * (x_i - 5*i)^2).
    """

    vector = np.asarray(x, dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError("x must be a non-empty one-dimensional vector")
    indices = np.arange(1, vector.size + 1, dtype=float)
    return float(np.sum(5.0 * indices * (vector - 5.0 * indices) ** 2))


@dataclass(frozen=True)
class GAResult:
    best_solution: np.ndarray
    best_value: float
    generations: int
    elapsed_seconds: float
    best_history: np.ndarray
    final_population: np.ndarray


def _check_probability(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")


def _clip(vector: np.ndarray, bounds: tuple[float, float]) -> np.ndarray:
    low, high = bounds
    return np.clip(vector, low, high)


def tournament_select(
    population: np.ndarray,
    values: np.ndarray,
    rng: np.random.Generator,
    tournament_size: int = 3,
) -> np.ndarray:
    """Select one individual for minimization by a tournament."""

    if tournament_size < 2:
        raise ValueError("tournament_size must be at least 2")
    candidates = rng.integers(0, len(population), size=tournament_size)
    winner = candidates[np.argmin(values[candidates])]
    return population[winner].copy()


def blx_alpha_crossover(
    parent_a: np.ndarray,
    parent_b: np.ndarray,
    rng: np.random.Generator,
    alpha: float = 0.5,
    bounds: tuple[float, float] = DEFAULT_BOUNDS,
) -> np.ndarray:
    """Create one child with the BLX-alpha real-valued crossover."""

    if alpha < 0.0:
        raise ValueError("alpha must be non-negative")
    lower = np.minimum(parent_a, parent_b)
    upper = np.maximum(parent_a, parent_b)
    span = upper - lower
    child = rng.uniform(lower - alpha * span, upper + alpha * span)
    return _clip(child, bounds)


def mutate(
    individual: np.ndarray,
    rng: np.random.Generator,
    mutation_probability: float,
    bounds: tuple[float, float] = DEFAULT_BOUNDS,
    scale: float = 0.10,
) -> np.ndarray:
    """Mutate genes with a bounded Gaussian perturbation."""

    _check_probability(mutation_probability, "mutation_probability")
    if scale <= 0.0:
        raise ValueError("scale must be positive")
    low, high = bounds
    result = individual.copy()
    mask = rng.random(result.size) < mutation_probability
    result[mask] += rng.normal(0.0, scale * (high - low), size=mask.sum())
    return _clip(result, bounds)


def run_ga(
    n: int,
    *,
    population_size: int = 80,
    crossover_probability: float = 0.90,
    mutation_probability: float = 0.08,
    max_generations: int = 500,
    patience: int = 80,
    tolerance: float = 1e-10,
    elite_count: int = 2,
    tournament_size: int = 3,
    alpha: float = 0.5,
    bounds: tuple[float, float] = DEFAULT_BOUNDS,
    seed: int | None = None,
) -> GAResult:
    """Run the real-coded GA and return the best individual and diagnostics."""

    _check_probability(crossover_probability, "crossover_probability")
    _check_probability(mutation_probability, "mutation_probability")
    if population_size < max(4, elite_count + 2):
        raise ValueError("population_size is too small")
    if max_generations < 1 or patience < 1:
        raise ValueError("max_generations and patience must be positive")
    if elite_count < 1 or elite_count >= population_size:
        raise ValueError("elite_count must be in [1, population_size)")
    low, high = bounds
    if low >= high:
        raise ValueError("bounds must be ordered as (low, high)")

    rng = np.random.default_rng(seed)
    population = rng.uniform(low, high, size=(population_size, n))
    best_solution = population[0].copy()
    best_value = float("inf")
    history: list[float] = []
    stagnant_generations = 0
    started = time.perf_counter()

    for generation in range(1, max_generations + 1):
        values = np.asarray(
            [moved_axis_parallel_hyperellipsoid(individual) for individual in population]
        )
        order = np.argsort(values)
        current_value = float(values[order[0]])
        if current_value < best_value - tolerance:
            best_value = current_value
            best_solution = population[order[0]].copy()
            stagnant_generations = 0
        else:
            stagnant_generations += 1
        history.append(best_value)

        if generation == max_generations or stagnant_generations >= patience:
            break

        next_population = [population[index].copy() for index in order[:elite_count]]
        while len(next_population) < population_size:
            parent_a = tournament_select(population, values, rng, tournament_size)
            parent_b = tournament_select(population, values, rng, tournament_size)
            if rng.random() < crossover_probability:
                child = blx_alpha_crossover(parent_a, parent_b, rng, alpha, bounds)
            else:
                child = parent_a
            next_population.append(mutate(child, rng, mutation_probability, bounds))
        population = np.asarray(next_population)

    return GAResult(
        best_solution=best_solution,
        best_value=best_value,
        generations=generation,
        elapsed_seconds=time.perf_counter() - started,
        best_history=np.asarray(history),
        final_population=population,
    )


def run_scipy_reference(
    n: int,
    *,
    population_size: int = 80,
    max_generations: int = 500,
    seed: int | None = None,
    bounds: tuple[float, float] = DEFAULT_BOUNDS,
) -> GAResult:
    """Run SciPy's independent differential-evolution reference optimizer."""

    from scipy.optimize import differential_evolution

    started = time.perf_counter()
    result = differential_evolution(
        moved_axis_parallel_hyperellipsoid,
        bounds=[bounds] * n,
        popsize=max(2, population_size // (15 * n)),
        maxiter=max_generations,
        polish=True,
        seed=seed,
        tol=1e-10,
        updating="immediate",
    )
    history = np.asarray([float(result.fun)])
    return GAResult(
        best_solution=np.asarray(result.x, dtype=float),
        best_value=float(result.fun),
        generations=int(result.nit),
        elapsed_seconds=time.perf_counter() - started,
        best_history=history,
        final_population=np.asarray([result.x], dtype=float),
    )
