"""Run the laboratory experiments and build report-ready figures."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics

import matplotlib.pyplot as plt
import numpy as np

from variant4_ga import (
    DEFAULT_BOUNDS,
    moved_axis_parallel_hyperellipsoid,
    run_ga,
    run_scipy_reference,
    target_point,
)


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_baseline() -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    summary: dict[str, object] = {}
    for n in (2, 3):
        ga_results = [
            run_ga(n=n, seed=1000 + n * 100 + repeat, max_generations=500)
            for repeat in range(10)
        ]
        reference_results = [
            run_scipy_reference(n=n, seed=2000 + n * 100 + repeat, max_generations=300)
            for repeat in range(5)
        ]
        for repeat, result in enumerate(ga_results):
            rows.append(
                {
                    "experiment": "baseline",
                    "algorithm": "custom_ga",
                    "n": n,
                    "repeat": repeat + 1,
                    "population_size": 80,
                    "crossover_probability": 0.90,
                    "mutation_probability": 0.08,
                    "generations": result.generations,
                    "elapsed_seconds": result.elapsed_seconds,
                    "best_value": result.best_value,
                    "distance_to_optimum": float(np.linalg.norm(result.best_solution - target_point(n))),
                    "best_solution": json.dumps(result.best_solution.tolist()),
                }
            )
        for repeat, result in enumerate(reference_results):
            rows.append(
                {
                    "experiment": "baseline",
                    "algorithm": "scipy_differential_evolution",
                    "n": n,
                    "repeat": repeat + 1,
                    "population_size": 80,
                    "crossover_probability": "",
                    "mutation_probability": "",
                    "generations": result.generations,
                    "elapsed_seconds": result.elapsed_seconds,
                    "best_value": result.best_value,
                    "distance_to_optimum": float(np.linalg.norm(result.best_solution - target_point(n))),
                    "best_solution": json.dumps(result.best_solution.tolist()),
                }
            )
        summary[str(n)] = {
            "custom_ga_best_value_median": statistics.median(r.best_value for r in ga_results),
            "custom_ga_time_median": statistics.median(r.elapsed_seconds for r in ga_results),
            "custom_ga_generations_median": statistics.median(r.generations for r in ga_results),
            "custom_ga_distance_median": statistics.median(
                float(np.linalg.norm(r.best_solution - target_point(n))) for r in ga_results
            ),
            "reference_best_value_median": statistics.median(r.best_value for r in reference_results),
            "reference_time_median": statistics.median(r.elapsed_seconds for r in reference_results),
            "reference_generations_median": statistics.median(r.generations for r in reference_results),
        }
    return rows, summary


def run_parameter_sweep() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    settings = [
        ("population", "population_size", value) for value in (30, 60, 120)
    ] + [
        ("crossover_probability", "crossover_probability", value) for value in (0.60, 0.80, 1.00)
    ] + [
        ("mutation_probability", "mutation_probability", value) for value in (0.02, 0.08, 0.20)
    ]
    for factor, parameter, value in settings:
        for repeat in range(8):
            kwargs = {
                "n": 2,
                "population_size": 80,
                "crossover_probability": 0.90,
                "mutation_probability": 0.08,
            }
            kwargs[parameter] = value
            result = run_ga(seed=3000 + len(rows), max_generations=400, **kwargs)
            rows.append(
                {
                    "experiment": factor,
                    "parameter": parameter,
                    "value": value,
                    "repeat": repeat + 1,
                    "generations": result.generations,
                    "elapsed_seconds": result.elapsed_seconds,
                    "best_value": result.best_value,
                    "distance_to_optimum": float(np.linalg.norm(result.best_solution - target_point(2))),
                }
            )
    return rows


def plot_convergence() -> None:
    result = run_ga(n=2, seed=4242, max_generations=400)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.semilogy(np.arange(1, result.generations + 1), np.maximum(result.best_history, 1e-12))
    ax.set_title("Сходимость ГА для варианта 4, n=2")
    ax.set_xlabel("Поколение")
    ax.set_ylabel("Лучшее значение целевой функции")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "convergence_n2.png", dpi=180)
    plt.close(fig)


def plot_surface_and_population() -> None:
    result = run_ga(n=2, seed=4242, max_generations=400)
    x1 = np.linspace(-5, 15, 180)
    x2 = np.linspace(-5, 20, 180)
    grid_x1, grid_x2 = np.meshgrid(x1, x2)
    grid_z = 5 * (grid_x1 - 5) ** 2 + 10 * (grid_x2 - 10) ** 2
    fig, ax = plt.subplots(figsize=(8, 6))
    levels = np.geomspace(1e-2, max(float(grid_z.max()), 1.0), 22)
    contour = ax.contourf(grid_x1, grid_x2, grid_z, levels=levels, norm="log", cmap="viridis")
    fig.colorbar(contour, ax=ax, label="f(x)")
    population = result.final_population
    ax.scatter(population[:, 0], population[:, 1], s=12, c="white", edgecolors="black", alpha=0.65, label="Финальная популяция")
    ax.scatter([5], [10], marker="*", s=180, c="red", edgecolors="black", label="Аналитический минимум")
    ax.scatter([result.best_solution[0]], [result.best_solution[1]], marker="X", s=100, c="orange", edgecolors="black", label="Лучшее решение ГА")
    ax.set_title("Поверхность функции и финальная популяция, n=2")
    ax.set_xlabel("x₁")
    ax.set_ylabel("x₂")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(RESULTS / "surface_n2_population.png", dpi=180)
    plt.close(fig)


def plot_parameter_sweep(rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(3, 3, figsize=(14, 11), sharex="col")
    titles = [
        ("population", "Размер популяции"),
        ("crossover_probability", "Вероятность кроссовера"),
        ("mutation_probability", "Вероятность мутации"),
    ]
    metric_titles = [
        ("elapsed_seconds", "Медиана времени, с"),
        ("generations", "Медиана числа поколений"),
        ("best_value", "Медиана f(x)"),
    ]
    for column, (factor, title) in enumerate(titles):
        groups = {}
        for row in rows:
            if row["experiment"] == factor:
                groups.setdefault(float(row["value"]), row)
        xs = sorted(groups)
        for row_index, (metric, metric_title) in enumerate(metric_titles):
            metric_groups = {}
            for row in rows:
                if row["experiment"] == factor:
                    metric_groups.setdefault(float(row["value"]), []).append(float(row[metric]))
            ax = axes[row_index, column]
            ys = [statistics.median(metric_groups[x]) for x in xs]
            ax.plot(xs, ys, marker="o")
            if row_index == 0:
                ax.set_title(title)
            if row_index == len(metric_titles) - 1:
                ax.set_xlabel("Значение параметра")
            ax.set_ylabel(metric_title)
            ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "parameter_sweep.png", dpi=180)
    plt.close(fig)


def main() -> None:
    baseline_rows, baseline_summary = run_baseline()
    sweep_rows = run_parameter_sweep()
    write_csv(RESULTS / "baseline_results.csv", baseline_rows)
    write_csv(RESULTS / "parameter_sweep.csv", sweep_rows)
    plot_convergence()
    plot_surface_and_population()
    plot_parameter_sweep(sweep_rows)
    summary = {
        "function": "sum(5*i*(x_i - 5*i)^2)",
        "bounds": list(DEFAULT_BOUNDS),
        "analytical_optimum": {str(n): target_point(n).tolist() for n in (2, 3)},
        "baseline": baseline_summary,
    }
    (RESULTS / "results_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
