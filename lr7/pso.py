"""Global-best particle swarm optimizer for the GUAP lab 7 benchmark."""

from __future__ import annotations

from dataclasses import dataclass
import random
import time
from typing import Callable


def moved_ellipsoid(position: list[float]) -> float:
    """Variant 4: sum(5*i*(x_i-5*i)^2), with i numbered from one."""
    return sum(5.0 * i * (x - 5.0 * i) ** 2 for i, x in enumerate(position, 1))


@dataclass
class SwarmResult:
    best_position: list[float]
    best_value: float
    best_history: list[float]
    mean_history: list[float]
    snapshots: dict[int, list[list[float]]]
    elapsed_seconds: float
    generations: int
    stop_reason: str


class ParticleSwarm:
    """Global-best PSO with inertia, bounded velocity, and reflective limits."""

    def __init__(
        self,
        dimensions: int,
        *,
        particles: int = 60,
        max_generations: int = 1000,
        patience: int = 100,
        tolerance: float = 1e-8,
        inertia: float = 0.7298,
        cognitive: float = 1.49618,
        social: float = 1.49618,
        lower: float = -55.0,
        upper: float = 55.0,
        seed: int = 2026,
        objective: Callable[[list[float]], float] = moved_ellipsoid,
    ) -> None:
        if dimensions < 2:
            raise ValueError("dimensions must be at least 2")
        if particles < 2 or max_generations < 1 or patience < 1:
            raise ValueError("particles, generations, and patience must be positive")
        if lower >= upper:
            raise ValueError("lower bound must be less than upper bound")
        self.dimensions = dimensions
        self.particles = particles
        self.max_generations = max_generations
        self.patience = patience
        self.tolerance = tolerance
        self.inertia = inertia
        self.cognitive = cognitive
        self.social = social
        self.lower = lower
        self.upper = upper
        self.seed = seed
        self.objective = objective
        self.rng = random.Random(seed)

    def run(self, *, capture: tuple[int, ...] = ()) -> SwarmResult:
        started = time.perf_counter()
        span = self.upper - self.lower
        velocity_limit = 0.2 * span
        positions = [
            [self.rng.uniform(self.lower, self.upper) for _ in range(self.dimensions)]
            for _ in range(self.particles)
        ]
        velocities = [
            [self.rng.uniform(-0.1 * span, 0.1 * span) for _ in range(self.dimensions)]
            for _ in range(self.particles)
        ]
        values = [self.objective(point) for point in positions]
        personal_positions = [point[:] for point in positions]
        personal_values = values[:]
        best_index = min(range(self.particles), key=personal_values.__getitem__)
        global_position = personal_positions[best_index][:]
        global_value = personal_values[best_index]
        best_history = [global_value]
        mean_history = [sum(values) / len(values)]
        snapshots: dict[int, list[list[float]]] = {0: [point[:] for point in positions]}
        stale = 0
        stop_reason = "достигнут предел поколений"
        generations = 0

        for generation in range(1, self.max_generations + 1):
            old_best = global_value
            for p in range(self.particles):
                for d in range(self.dimensions):
                    r1 = self.rng.random()
                    r2 = self.rng.random()
                    velocities[p][d] = (
                        self.inertia * velocities[p][d]
                        + self.cognitive * r1 * (personal_positions[p][d] - positions[p][d])
                        + self.social * r2 * (global_position[d] - positions[p][d])
                    )
                    velocities[p][d] = max(-velocity_limit, min(velocity_limit, velocities[p][d]))
                    candidate = positions[p][d] + velocities[p][d]
                    if candidate < self.lower:
                        candidate = self.lower + (self.lower - candidate)
                        velocities[p][d] *= -0.5
                    elif candidate > self.upper:
                        candidate = self.upper - (candidate - self.upper)
                        velocities[p][d] *= -0.5
                    positions[p][d] = max(self.lower, min(self.upper, candidate))

                values[p] = self.objective(positions[p])
                if values[p] < personal_values[p]:
                    personal_values[p] = values[p]
                    personal_positions[p] = positions[p][:]
                    if values[p] < global_value:
                        global_value = values[p]
                        global_position = positions[p][:]

            generations = generation
            best_history.append(global_value)
            mean_history.append(sum(values) / len(values))
            if generation in capture:
                snapshots[generation] = [point[:] for point in positions]
            if global_value <= self.tolerance:
                stop_reason = f"достигнута точность f ≤ {self.tolerance:g}"
                break
            if global_value < old_best - max(1e-14, abs(old_best) * 1e-12):
                stale = 0
            else:
                stale += 1
            if stale >= self.patience:
                stop_reason = f"нет улучшения {self.patience} поколений"
                break

        if generations not in snapshots:
            snapshots[generations] = [point[:] for point in positions]
        return SwarmResult(
            best_position=global_position,
            best_value=global_value,
            best_history=best_history,
            mean_history=mean_history,
            snapshots=snapshots,
            elapsed_seconds=time.perf_counter() - started,
            generations=generations,
            stop_reason=stop_reason,
        )
