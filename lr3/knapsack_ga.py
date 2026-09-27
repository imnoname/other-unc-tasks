"""Binary genetic algorithm for 0/1 knapsack benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
import random
from time import perf_counter
from typing import Iterable

from data import KnapsackProblem


@dataclass(frozen=True)
class Evaluation:
    chromosome: tuple[int, ...]
    weight: int
    profit: int


@dataclass(frozen=True)
class GARun:
    problem: str
    best: Evaluation
    history: tuple[int, ...]
    elapsed_seconds: float
    seed: int
    parameters: dict[str, float | int | str]


def _validate_chromosome(chromosome: Iterable[int], problem: KnapsackProblem) -> tuple[int, ...]:
    result = tuple(int(gene) for gene in chromosome)
    if len(result) != len(problem.weights):
        raise ValueError("chromosome length must equal the number of items")
    if any(gene not in (0, 1) for gene in result):
        raise ValueError("binary chromosome genes must be 0 or 1")
    return result


def repair(chromosome: Iterable[int], problem: KnapsackProblem) -> Evaluation:
    """Repair an overweight chromosome by removing the least profitable density items."""
    genes = list(_validate_chromosome(chromosome, problem))
    weight = sum(gene * item_weight for gene, item_weight in zip(genes, problem.weights))
    while weight > problem.capacity:
        selected = [i for i, gene in enumerate(genes) if gene]
        if not selected:
            break
        index = min(
            selected,
            key=lambda i: (problem.profits[i] / problem.weights[i], problem.profits[i], -i)
            if problem.weights[i]
            else (-float("inf"), problem.profits[i], -i),
        )
        genes[index] = 0
        weight -= problem.weights[index]
    profit = sum(gene * item_profit for gene, item_profit in zip(genes, problem.profits))
    return Evaluation(tuple(genes), weight, profit)


def evaluate(chromosome: Iterable[int], problem: KnapsackProblem) -> Evaluation:
    return repair(chromosome, problem)


def exact_optimum(problem: KnapsackProblem) -> Evaluation:
    """Solve the benchmark exactly with 0/1 dynamic programming for validation."""
    capacity = problem.capacity
    values = [0] * (capacity + 1)
    choices: list[bytearray] = [bytearray(capacity + 1) for _ in problem.weights]
    for index, (weight, profit) in enumerate(zip(problem.weights, problem.profits)):
        for current in range(capacity, weight - 1, -1):
            candidate = values[current - weight] + profit
            if candidate > values[current]:
                values[current] = candidate
                choices[index][current] = 1

    chromosome = [0] * len(problem.weights)
    current = capacity
    for index in range(len(problem.weights) - 1, -1, -1):
        if choices[index][current]:
            chromosome[index] = 1
            current -= problem.weights[index]
    return evaluate(chromosome, problem)


def _tournament(population: list[Evaluation], rng: random.Random, size: int = 3) -> Evaluation:
    contestants = [population[rng.randrange(len(population))] for _ in range(size)]
    return max(contestants, key=lambda individual: individual.profit)


def _crossover(
    first: tuple[int, ...],
    second: tuple[int, ...],
    rng: random.Random,
    method: str,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if len(first) < 2:
        return first, second
    if method == "two_point" and len(first) >= 3:
        left, right = sorted(rng.sample(range(1, len(first)), 2))
        child_a = first[:left] + second[left:right] + first[right:]
        child_b = second[:left] + first[left:right] + second[right:]
    else:
        point = rng.randrange(1, len(first))
        child_a = first[:point] + second[point:]
        child_b = second[:point] + first[point:]
    return child_a, child_b


def _mutate(chromosome: tuple[int, ...], rng: random.Random, probability: float) -> tuple[int, ...]:
    return tuple(1 - gene if rng.random() < probability else gene for gene in chromosome)


def genetic_algorithm(
    problem: KnapsackProblem,
    *,
    population_size: int = 60,
    generations: int = 250,
    crossover_probability: float = 0.85,
    mutation_probability: float | None = None,
    crossover_method: str = "two_point",
    elite_size: int = 2,
    seed: int = 0,
) -> GARun:
    if population_size < 2 or generations < 1:
        raise ValueError("population_size must be >= 2 and generations must be >= 1")
    if not 0 <= crossover_probability <= 1 or not 0 <= elite_size < population_size:
        raise ValueError("invalid crossover probability or elite size")
    if mutation_probability is None:
        mutation_probability = 1 / len(problem.weights)
    if not 0 <= mutation_probability <= 1:
        raise ValueError("mutation probability must be between 0 and 1")
    if crossover_method not in {"one_point", "two_point"}:
        raise ValueError("unsupported crossover method")

    rng = random.Random(seed)
    started = perf_counter()
    population = [
        evaluate((rng.randrange(2) for _ in problem.weights), problem)
        for _ in range(population_size)
    ]
    best = max(population, key=lambda individual: individual.profit)
    history = [best.profit]

    for _ in range(generations):
        ordered = sorted(population, key=lambda individual: individual.profit, reverse=True)
        next_population = ordered[:elite_size]
        while len(next_population) < population_size:
            parent_a = _tournament(population, rng)
            parent_b = _tournament(population, rng)
            child_a, child_b = parent_a.chromosome, parent_b.chromosome
            if rng.random() < crossover_probability:
                child_a, child_b = _crossover(child_a, child_b, rng, crossover_method)
            child_a = _mutate(child_a, rng, mutation_probability)
            next_population.append(evaluate(child_a, problem))
            if len(next_population) < population_size:
                child_b = _mutate(child_b, rng, mutation_probability)
                next_population.append(evaluate(child_b, problem))
        population = next_population
        current = max(population, key=lambda individual: individual.profit)
        if current.profit > best.profit:
            best = current
        history.append(best.profit)

    return GARun(
        problem=problem.name,
        best=best,
        history=tuple(history),
        elapsed_seconds=perf_counter() - started,
        seed=seed,
        parameters={
            "population_size": population_size,
            "generations": generations,
            "crossover_probability": crossover_probability,
            "mutation_probability": mutation_probability,
            "crossover_method": crossover_method,
            "elite_size": elite_size,
        },
    )
