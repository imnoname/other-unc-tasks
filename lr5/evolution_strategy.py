"""Evolution strategy for GUAP laboratory work 5, variant 4."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable


def objective(vector: Iterable[float]) -> float:
    """Printed variant-4 formula: sum(5*i*x_i^2), i starts at one."""
    return sum(5.0 * (index + 1) * value * value for index, value in enumerate(vector))


@dataclass
class Individual:
    x: list[float]
    sigma: list[float]
    value: float

    def clone(self) -> "Individual":
        return Individual(self.x[:], self.sigma[:], self.value)


@dataclass
class RunResult:
    dimension: int
    best: Individual
    history: list[dict]
    snapshots: list[list[Individual]]
    elapsed_seconds: float
    stopped_generation: int


class EvolutionStrategy:
    """Self-adaptive (mu+lambda)-ES with real-valued phenotype mutation."""

    def __init__(self, dimension: int, population_size: int = 20, offspring_count: int | None = None,
                 mutation_probability: float = 1.0, bounds: tuple[float, float] = (-5.12, 5.12),
                 max_generations: int = 100, stagnation_limit: int = 25, seed: int = 4):
        self.dimension = dimension
        self.population_size = population_size
        self.offspring_count = offspring_count or population_size
        self.mutation_probability = mutation_probability
        self.lower, self.upper = bounds
        self.max_generations = max_generations
        self.stagnation_limit = stagnation_limit
        self.rng = random.Random(seed)
        self.tau = 1.0 / math.sqrt(2.0 * math.sqrt(dimension))
        self.tau_prime = 1.0 / math.sqrt(2.0 * dimension)

    def make_individual(self) -> Individual:
        x = [self.rng.uniform(self.lower, self.upper) for _ in range(self.dimension)]
        sigma = [(self.upper - self.lower) * 0.2 for _ in range(self.dimension)]
        return Individual(x, sigma, objective(x))

    def mutate(self, parent: Individual) -> Individual:
        if self.rng.random() > self.mutation_probability:
            return parent.clone()
        common = self.rng.gauss(0.0, 1.0)
        sigma = []
        x = []
        for value, step in zip(parent.x, parent.sigma):
            new_step = step * math.exp(self.tau_prime * common + self.tau * self.rng.gauss(0.0, 1.0))
            new_step = max(1e-8, min(self.upper - self.lower, new_step))
            new_value = value + new_step * self.rng.gauss(0.0, 1.0)
            x.append(max(self.lower, min(self.upper, new_value)))
            sigma.append(new_step)
        return Individual(x, sigma, objective(x))

    def run(self) -> RunResult:
        import time

        started = time.perf_counter()
        population = [self.make_individual() for _ in range(self.population_size)]
        best = min(population, key=lambda individual: individual.value).clone()
        history: list[dict] = []
        snapshots: list[list[Individual]] = []
        stagnant = 0
        for generation in range(self.max_generations + 1):
            population.sort(key=lambda individual: individual.value)
            if population[0].value < best.value:
                best = population[0].clone()
                stagnant = 0
            else:
                stagnant += 1
            history.append({
                "generation": generation,
                "best_value": best.value,
                "mean_value": sum(item.value for item in population) / len(population),
                "distance": math.sqrt(sum(value * value for value in best.x)),
                "sigma_mean": sum(best.sigma) / len(best.sigma),
            })
            if generation % 10 == 0 or generation == self.max_generations:
                snapshots.append([item.clone() for item in population])
            if generation == self.max_generations or stagnant >= self.stagnation_limit or best.value < 1e-12:
                break
            offspring = [self.mutate(self.rng.choice(population)) for _ in range(self.offspring_count)]
            population = sorted(population + offspring, key=lambda individual: individual.value)[: self.population_size]
        return RunResult(self.dimension, best, history, snapshots, time.perf_counter() - started, generation)

