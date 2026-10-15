"""Tree-based genetic programming for symbolic regression, laboratory work 4."""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass
from typing import Callable, Iterable


TARGET_FORMULA = "x^6 - 2*x^4 + x^2"


def target_function(x: float) -> float:
    return x**6 - 2.0 * x**4 + x**2


@dataclass
class Node:
    """A program tree node. Terminals have op='x' or op='const'."""

    op: str
    children: list["Node"]
    value: float | None = None

    def clone(self) -> "Node":
        return copy.deepcopy(self)

    def size(self) -> int:
        return 1 + sum(child.size() for child in self.children)

    def depth(self) -> int:
        return 1 if not self.children else 1 + max(child.depth() for child in self.children)


FUNCTION_ARITY: dict[str, int] = {
    "+": 2,
    "-": 2,
    "*": 2,
    "/": 2,
    "pow": 2,
    "abs": 1,
    "sin": 1,
    "cos": 1,
    "exp": 1,
    "sqrt": 1,
    "pow2": 1,
    "pow4": 1,
    "pow6": 1,
}


def protected_div(a: float, b: float) -> float:
    return a / b if abs(b) > 1e-9 else a


def safe_pow(a: float, b: float) -> float:
    if not math.isfinite(a) or not math.isfinite(b):
        return 0.0
    exponent = max(-6, min(6, int(round(b))))
    try:
        value = a**exponent
    except (OverflowError, ZeroDivisionError):
        return 0.0
    return value if math.isfinite(value) else 0.0


def evaluate(node: Node, x: float) -> float:
    if node.op == "x":
        return x
    if node.op == "const":
        return float(node.value or 0.0)
    values = [evaluate(child, x) for child in node.children]
    try:
        if node.op == "+":
            value = values[0] + values[1]
        elif node.op == "-":
            value = values[0] - values[1]
        elif node.op == "*":
            value = values[0] * values[1]
        elif node.op == "/":
            value = protected_div(values[0], values[1])
        elif node.op == "pow":
            value = safe_pow(values[0], values[1])
        elif node.op == "abs":
            value = abs(values[0])
        elif node.op == "sin":
            value = math.sin(values[0])
        elif node.op == "cos":
            value = math.cos(values[0])
        elif node.op == "exp":
            value = math.exp(max(-8.0, min(8.0, values[0])))
        elif node.op == "sqrt":
            value = math.sqrt(abs(values[0]))
        elif node.op == "pow2":
            value = values[0] ** 2
        elif node.op == "pow4":
            value = values[0] ** 4
        elif node.op == "pow6":
            value = values[0] ** 6
        else:
            raise ValueError(f"Unknown operation: {node.op}")
    except (OverflowError, ZeroDivisionError, ValueError):
        return 0.0
    return float(value) if math.isfinite(value) else 0.0


def expression(node: Node) -> str:
    if node.op == "x":
        return "x"
    if node.op == "const":
        value = float(node.value or 0.0)
        return str(int(value)) if value.is_integer() else f"{value:.3g}"
    if node.op in {"+", "-", "*", "/", "pow"}:
        symbol = "^" if node.op == "pow" else node.op
        return f"({expression(node.children[0])} {symbol} {expression(node.children[1])})"
    return f"{node.op}({expression(node.children[0])})"


def all_paths(node: Node, path: tuple[int, ...] = ()) -> list[tuple[int, ...]]:
    paths = [path]
    for index, child in enumerate(node.children):
        paths.extend(all_paths(child, path + (index,)))
    return paths


def get_subtree(node: Node, path: tuple[int, ...]) -> Node:
    current = node
    for index in path:
        current = current.children[index]
    return current


def replace_subtree(node: Node, path: tuple[int, ...], replacement: Node) -> Node:
    if not path:
        return replacement.clone()
    result = node.clone()
    parent = result
    for index in path[:-1]:
        parent = parent.children[index]
    parent.children[path[-1]] = replacement.clone()
    return result


class GeneticProgramming:
    """A compact generational GP implementation with tree crossover and mutation."""

    def __init__(
        self,
        x_values: Iterable[float],
        y_values: Iterable[float],
        population_size: int = 500,
        generations: int = 150,
        max_depth: int = 7,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.12,
        tournament_size: int = 5,
        parsimony: float = 1e-5,
        seed: int = 4,
    ):
        self.x_values = list(x_values)
        self.y_values = list(y_values)
        self.population_size = population_size
        self.generations = generations
        self.max_depth = max_depth
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.parsimony = parsimony
        self.rng = random.Random(seed)
        self.history: list[dict[str, float | int | str]] = []
        self.snapshots: list[tuple[int, Node]] = []
        self.all_snapshots: list[tuple[int, Node]] = []

    def random_terminal(self) -> Node:
        if self.rng.random() < 0.65:
            return Node("x", [])
        return Node("const", [], float(self.rng.choice(list(range(-5, 6)))))

    def random_tree(self, depth: int, full: bool = False) -> Node:
        if depth <= 0 or (not full and depth > 1 and self.rng.random() < 0.35):
            return self.random_terminal()
        # The restricted power functions are equivalent to exponentiation by a
        # small integer and make the variant's polynomial representable compactly.
        weighted = ["+", "-", "*", "/", "pow", "abs", "sin", "cos", "exp", "sqrt", "pow2", "pow4", "pow6"]
        op = self.rng.choice(weighted)
        return Node(op, [self.random_tree(depth - 1, full) for _ in range(FUNCTION_ARITY[op])])

    def initial_population(self) -> list[Node]:
        return [self.random_tree(self.rng.randint(2, self.max_depth), i % 2 == 0) for i in range(self.population_size)]

    def mse(self, node: Node) -> float:
        errors = []
        for x, y in zip(self.x_values, self.y_values):
            predicted = evaluate(node, x)
            if not math.isfinite(predicted) or abs(predicted) > 1e6:
                return 1e6
            errors.append((predicted - y) ** 2)
        return sum(errors) / len(errors)

    def score(self, node: Node) -> float:
        return self.mse(node) + self.parsimony * node.size()

    def select(self, population: list[Node], scores: list[float]) -> Node:
        indices = [self.rng.randrange(len(population)) for _ in range(self.tournament_size)]
        return population[min(indices, key=lambda index: scores[index])]

    def mutate(self, node: Node) -> Node:
        paths = all_paths(node)
        path = self.rng.choice(paths)
        replacement_depth = max(0, self.max_depth - len(path) - 1)
        replacement = self.random_tree(self.rng.randint(0, replacement_depth), full=False)
        return replace_subtree(node, path, replacement)

    def crossover(self, first: Node, second: Node) -> tuple[Node, Node]:
        first_path = self.rng.choice(all_paths(first))
        second_path = self.rng.choice(all_paths(second))
        left = replace_subtree(first, first_path, get_subtree(second, second_path))
        right = replace_subtree(second, second_path, get_subtree(first, first_path))
        if left.depth() > self.max_depth:
            left = first.clone()
        if right.depth() > self.max_depth:
            right = second.clone()
        return left, right

    def run(self) -> tuple[Node, float]:
        population = self.initial_population()
        best = min(population, key=self.score).clone()
        for generation in range(self.generations + 1):
            scores = [self.score(individual) for individual in population]
            generation_best_index = min(range(len(population)), key=lambda i: scores[i])
            generation_best = population[generation_best_index]
            if self.score(generation_best) < self.score(best):
                best = generation_best.clone()
            best_mse = self.mse(best)
            self.history.append({
                "generation": generation,
                "mse": best_mse,
                "score": self.score(best),
                "size": best.size(),
                "depth": best.depth(),
                "formula": expression(best),
            })
            self.all_snapshots.append((generation, best.clone()))
            if generation in {0, 10, 25, 50, 100, self.generations}:
                self.snapshots.append((generation, best.clone()))
            if generation == self.generations:
                break
            next_population = [best.clone()]
            while len(next_population) < self.population_size:
                first = self.select(population, scores).clone()
                second = self.select(population, scores).clone()
                if self.rng.random() < self.crossover_rate:
                    first, second = self.crossover(first, second)
                if self.rng.random() < self.mutation_rate:
                    first = self.mutate(first)
                if self.rng.random() < self.mutation_rate:
                    second = self.mutate(second)
                next_population.extend((first, second))
            population = next_population[: self.population_size]
        return best, self.mse(best)


def make_training_data(seed: int = 4) -> tuple[list[float], list[float]]:
    rng = random.Random(seed)
    x_values = sorted(rng.uniform(-1.0, 1.0) for _ in range(20))
    return x_values, [target_function(x) for x in x_values]

