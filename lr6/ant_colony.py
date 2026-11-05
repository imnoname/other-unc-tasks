"""Ant colony optimization for open Hamiltonian paths and TSP cycles."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass


def validate_route(route: list[int], city_count: int) -> bool:
    return len(route) == city_count and set(route) == set(range(city_count))


def route_length(route: list[int], distances: list[list[float]], closed: bool) -> float:
    total = sum(distances[a][b] for a, b in zip(route, route[1:]))
    if closed and len(route) > 1:
        total += distances[route[-1]][route[0]]
    return total


@dataclass
class ColonyResult:
    route: list[int]
    length: float
    closed: bool
    history: list[dict]
    elapsed_seconds: float


class AntColony:
    def __init__(self, distances: list[list[float]], ants: int = 40, iterations: int = 300,
                 alpha: float = 1.0, beta: float = 3.0, evaporation: float = 0.35,
                 q: float = 100.0, seed: int = 4):
        self.distances = distances
        self.n = len(distances)
        if self.n < 2 or any(len(row) != self.n for row in distances):
            raise ValueError("distance matrix must be square and contain at least two cities")
        if not 0 < evaporation < 1:
            raise ValueError("evaporation must be between 0 and 1")
        self.ants = ants
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation
        self.q = q
        self.rng = random.Random(seed)

    def _construct(self, pheromone: list[list[float]], closed: bool) -> list[int]:
        route = [self.rng.randrange(self.n)]
        remaining = set(range(self.n)) - set(route)
        while remaining:
            current = route[-1]
            candidates = sorted(remaining)
            weights = []
            for city in candidates:
                distance = max(self.distances[current][city], 1e-12)
                weights.append((pheromone[current][city] ** self.alpha) * ((1.0 / distance) ** self.beta))
            total = sum(weights)
            if total <= 0 or not math.isfinite(total):
                next_city = self.rng.choice(candidates)
            else:
                threshold = self.rng.random() * total
                next_city = candidates[-1]
                for city, weight in zip(candidates, weights):
                    threshold -= weight
                    if threshold <= 0:
                        next_city = city
                        break
            route.append(next_city)
            remaining.remove(next_city)
        return route

    def run(self, closed: bool = True) -> ColonyResult:
        started = time.perf_counter()
        initial_pheromone = 1.0 / (self.n * max(sum(min(row[j] for j in range(self.n) if j != i) for i, row in enumerate(self.distances)) / self.n, 1e-9))
        pheromone = [[initial_pheromone if i != j else 0.0 for j in range(self.n)] for i in range(self.n)]
        best_route: list[int] | None = None
        best_length = math.inf
        history = []
        for iteration in range(1, self.iterations + 1):
            routes = []
            for _ in range(self.ants):
                route = self._construct(pheromone, closed)
                length = route_length(route, self.distances, closed)
                routes.append((route, length))
                if length < best_length:
                    best_route, best_length = route, length
            for i in range(self.n):
                for j in range(self.n):
                    pheromone[i][j] *= (1.0 - self.evaporation)
            for route, length in routes:
                deposit = self.q / max(length, 1e-12)
                edges = list(zip(route, route[1:]))
                if closed:
                    edges.append((route[-1], route[0]))
                for a, b in edges:
                    pheromone[a][b] += deposit
                    pheromone[b][a] += deposit
            history.append({"iteration": iteration, "best_length": best_length,
                            "iteration_best": min(length for _, length in routes),
                            "mean_length": sum(length for _, length in routes) / len(routes)})
        assert best_route is not None
        return ColonyResult(best_route, best_length, closed, history, time.perf_counter() - started)
