"""Real-valued genetic algorithm for the two-parameter COCOMO model."""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Callable, Sequence

A_BOUNDS = (0.05, 20.0)
B_BOUNDS = (0.1, 2.5)


@dataclass(frozen=True)
class FitResult:
    a: float
    b: float
    error: float
    history: tuple[float, ...]


def cocomo_effort(kloc: float, a: float, b: float) -> float:
    if kloc <= 0 or a <= 0:
        raise ValueError("KLOC and coefficient a must be positive")
    return a * kloc**b


def absolute_error_rms(actual: Sequence[float], predicted: Sequence[float]) -> float:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("actual and predicted must have the same non-zero length")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(actual, predicted)) / len(actual))


def predict(kloc: Sequence[float], a: float, b: float) -> list[float]:
    return [cocomo_effort(size, a, b) for size in kloc]


def _score(candidate: tuple[float, float], kloc: Sequence[float], effort: Sequence[float]) -> float:
    try:
        predictions = predict(kloc, *candidate)
        if not all(math.isfinite(value) for value in predictions):
            return math.inf
        return absolute_error_rms(effort, predictions)
    except (OverflowError, ValueError):
        return math.inf


def _roulette(population: list[tuple[float, float]], errors: list[float], rng: random.Random) -> tuple[float, float]:
    finite = [e for e in errors if math.isfinite(e)]
    if not finite:
        return rng.choice(population)
    worst = max(finite)
    weights = [max(0.0, worst - e) + 1e-12 if math.isfinite(e) else 0.0 for e in errors]
    return rng.choices(population, weights=weights, k=1)[0]


def fit_genetic_algorithm(
    kloc: Sequence[float],
    effort: Sequence[float],
    *,
    population_size: int = 100,
    generations: int = 400,
    crossover_probability: float = 0.9,
    mutation_probability: float = 0.15,
    seed: int = 42,
    a_bounds: tuple[float, float] = A_BOUNDS,
    b_bounds: tuple[float, float] = B_BOUNDS,
    on_generation: Callable[[int, float], None] | None = None,
) -> FitResult:
    """Minimize the RMS/ED on a training set using roulette selection and real coding."""
    if len(kloc) != len(effort) or len(kloc) < 2:
        raise ValueError("at least two paired observations are required")
    if any(x <= 0 for x in kloc) or any(y < 0 for y in effort):
        raise ValueError("KLOC must be positive and effort non-negative")
    if population_size < 4 or generations < 1:
        raise ValueError("population_size must be >= 4 and generations >= 1")
    if not 0 <= crossover_probability <= 1 or not 0 <= mutation_probability <= 1:
        raise ValueError("operator probabilities must be in [0, 1]")
    if not (0 < a_bounds[0] < a_bounds[1] and 0 < b_bounds[0] < b_bounds[1]):
        raise ValueError("parameter bounds must be positive and increasing")

    rng = random.Random(seed)
    bounds = (a_bounds, b_bounds)
    spans = tuple(high - low for low, high in bounds)
    population = [tuple(rng.uniform(low, high) for low, high in bounds) for _ in range(population_size)]
    history: list[float] = []

    for generation in range(generations + 1):
        errors = [_score(individual, kloc, effort) for individual in population]
        best_index = min(range(population_size), key=errors.__getitem__)
        best_error = errors[best_index]
        history.append(best_error)
        if on_generation:
            on_generation(generation, best_error)
        if generation == generations:
            break

        next_population = [population[best_index]]  # elitism protects the current best
        while len(next_population) < population_size:
            parent1 = _roulette(population, errors, rng)
            parent2 = _roulette(population, errors, rng)
            if rng.random() < crossover_probability:
                alpha = rng.random()
                child = tuple(alpha * p1 + (1.0 - alpha) * p2 for p1, p2 in zip(parent1, parent2))
            else:
                child = parent1
            genes = list(child)
            for gene_index, (low, high) in enumerate(bounds):
                if rng.random() < mutation_probability:
                    # Arithmetic mutation: add a bounded real-valued perturbation.
                    genes[gene_index] += rng.gauss(0.0, spans[gene_index] * 0.06)
                genes[gene_index] = min(high, max(low, genes[gene_index]))
            next_population.append((genes[0], genes[1]))
        population = next_population

    best_index = min(range(population_size), key=lambda i: _score(population[i], kloc, effort))
    best_a, best_b = population[best_index]
    return FitResult(best_a, best_b, _score((best_a, best_b), kloc, effort), tuple(history))
