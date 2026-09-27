"""Run reproducible experiments for laboratory work 3."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics
import sys

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data import P04, SET7, KnapsackProblem
from knapsack_ga import GARun, exact_optimum, genetic_algorithm


RESULTS = ROOT / "results"
BASELINE = {
    P04.name: {"population_size": 60, "generations": 250, "seeds": range(5)},
    SET7.name: {"population_size": 100, "generations": 400, "seeds": range(5)},
}


def run_once(problem: KnapsackProblem, seed: int, **overrides: int | float | str) -> GARun:
    parameters = dict(BASELINE[problem.name])
    parameters.pop("seeds")
    parameters.update(overrides)
    return genetic_algorithm(problem, seed=seed, **parameters)


def as_result(problem: KnapsackProblem, run: GARun, optimum: int, label: str) -> dict:
    return {
        "problem": problem.name,
        "label": label,
        "seed": run.seed,
        "profit": run.best.profit,
        "weight": run.best.weight,
        "capacity": problem.capacity,
        "error": optimum - run.best.profit,
        "accuracy_percent": 100 * run.best.profit / optimum if optimum else 100.0,
        "elapsed_seconds": run.elapsed_seconds,
        "chromosome": list(run.best.chromosome),
        "parameters": run.parameters,
    }


def summarize(rows: list[dict]) -> dict:
    profits = [row["profit"] for row in rows]
    accuracies = [row["accuracy_percent"] for row in rows]
    return {
        "runs": len(rows),
        "best_profit": max(profits),
        "mean_profit": statistics.mean(profits),
        "stdev_profit": statistics.stdev(profits) if len(profits) > 1 else 0.0,
        "mean_accuracy_percent": statistics.mean(accuracies),
        "mean_time_seconds": statistics.mean(row["elapsed_seconds"] for row in rows),
    }


def save_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "problem", "label", "seed", "profit", "weight", "capacity", "error",
        "accuracy_percent", "elapsed_seconds",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)


def plot_convergence(problem: KnapsackProblem, runs: list[GARun], optimum: int) -> None:
    plt.figure(figsize=(8, 4.8))
    for run in runs:
        plt.plot(run.history, linewidth=1.2, alpha=0.75, label=f"seed {run.seed}")
    plt.axhline(optimum, color="black", linestyle="--", linewidth=1.0, label="точный оптимум")
    plt.title(f"Сходимость ГА: {problem.name}")
    plt.xlabel("Поколение")
    plt.ylabel("Стоимость решения")
    plt.grid(alpha=0.25)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(RESULTS / f"convergence_{problem.name.replace(' ', '_').lower()}.png", dpi=180)
    plt.close()


def parameter_study(problem: KnapsackProblem, optimum: int) -> list[dict]:
    rows: list[dict] = []
    base = BASELINE[problem.name]
    studies = [
        ("population", "population_size", [20, 60, 100]),
        ("crossover", "crossover_probability", [0.60, 0.85, 1.00]),
        ("mutation", "mutation_probability", [0.005, 0.02, 0.05]),
    ]
    for label, parameter, values in studies:
        for value in values:
            for seed in range(3):
                overrides = {parameter: value}
                if parameter == "population_size":
                    overrides["generations"] = base["generations"]
                run = run_once(problem, seed, **overrides)
                rows.append(as_result(problem, run, optimum, f"{label}={value}"))
    return rows


def plot_parameter_study(rows: list[dict], problem: KnapsackProblem, label: str, filename: str) -> None:
    selected = [row for row in rows if row["problem"] == problem.name and row["label"].startswith(label + "=")]
    values = []
    means = []
    accuracies = []
    for row in selected:
        value = row["label"].split("=", 1)[1]
        if value not in values:
            values.append(value)
            group = [item for item in selected if item["label"] == row["label"]]
            means.append(statistics.mean(item["profit"] for item in group))
            accuracies.append(statistics.mean(item["accuracy_percent"] for item in group))
    x = list(range(len(values)))
    fig, axis = plt.subplots(figsize=(8, 4.8))
    axis.plot(x, means, marker="o", label="средняя стоимость")
    axis.set_xticks(x, values)
    axis.set_xlabel(label)
    axis.set_ylabel("Средняя стоимость")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / filename, dpi=180)
    plt.close(fig)


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    problems = (P04, SET7)
    exact = {problem.name: exact_optimum(problem) for problem in problems}
    baseline_rows: list[dict] = []
    all_runs: dict[str, list[GARun]] = {}
    summaries: dict[str, dict] = {}

    for problem in problems:
        runs = [run_once(problem, seed) for seed in BASELINE[problem.name]["seeds"]]
        all_runs[problem.name] = runs
        rows = [as_result(problem, run, exact[problem.name].profit, "baseline") for run in runs]
        baseline_rows.extend(rows)
        summaries[problem.name] = {
            "exact": {
                "profit": exact[problem.name].profit,
                "weight": exact[problem.name].weight,
                "chromosome": list(exact[problem.name].chromosome),
            },
            "baseline": summarize(rows),
        }
        plot_convergence(problem, runs, exact[problem.name].profit)

    study_rows = []
    for problem in problems:
        study_rows.extend(parameter_study(problem, exact[problem.name].profit))
    save_csv(RESULTS / "baseline.csv", baseline_rows)
    save_csv(RESULTS / "parameter_study.csv", study_rows)
    for label, filename in (
        ("population", "parameter_population.png"),
        ("crossover", "parameter_crossover.png"),
        ("mutation", "parameter_mutation.png"),
    ):
        plot_parameter_study(study_rows, SET7, label, filename)

    summaries["parameter_study"] = {
        "rows": len(study_rows),
        "best": max(study_rows, key=lambda row: row["profit"]),
    }
    with (RESULTS / "results_summary.json").open("w", encoding="utf-8") as stream:
        json.dump({"problems": summaries}, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"problems": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
