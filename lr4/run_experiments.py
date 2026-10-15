"""Run reproducible GP experiments and create report figures."""

from __future__ import annotations

import csv
import json
import math
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from gp_symbolic_regression import GeneticProgramming, evaluate, expression, make_training_data, target_function


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_convergence(history: list[dict], path: Path) -> None:
    canvas = Image.new("RGB", (1200, 650), "white")
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = 100, 70, 1130, 560
    draw.rectangle((left, top, right, bottom), outline="#444444", width=2)
    values = [max(float(row["mse"]), 1e-12) for row in history]
    logs = [math.log10(value) for value in values]
    lo, hi = min(logs), max(logs)
    if abs(hi - lo) < 1e-9:
        hi = lo + 1
    points = []
    for row, value in zip(history, logs):
        px = left + (right - left) * row["generation"] / max(1, history[-1]["generation"])
        py = bottom - (bottom - top) * (value - lo) / (hi - lo)
        points.append((px, py))
    draw.line(points, fill="#1f4e79", width=4)
    draw.text((left, 20), "Сходимость генетического программирования", fill="black")
    draw.text((left, 580), "Поколение", fill="black")
    draw.text((10, top), "log10(MSE)", fill="black")
    canvas.save(path)


def draw_tree(node, ax, x: float, y: float, dx: float, level: int = 0, parent=None) -> None:
    label = node.op if node.op != "const" else str(int(node.value or 0))
    if node.op == "x":
        label = "x"
    draw = ax[0]
    draw.rounded_rectangle((x - 28, y - 14, x + 28, y + 14), radius=5, fill="#eaf2f8", outline="#4f81bd")
    draw.text((x - 20, y - 8), label, fill="black")
    if parent is not None:
        draw.line((parent[0], parent[1] + 14, x, y - 14), fill="#777777", width=2)
    if node.children:
        width = dx * (len(node.children) - 1)
        for index, child in enumerate(node.children):
            child_x = x - width / 2 + index * dx
            draw_tree(child, ax, child_x, y + 75, dx * 0.68, level + 1, (x, y))


def plot_tree(node, generation: int, path: Path) -> None:
    canvas = Image.new("RGB", (1400, 700), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 20), f"Лучшее дерево, поколение {generation}: {expression(node)}", fill="black")
    draw_tree(node, (draw, canvas), 700, 90, 310)
    canvas.save(path)


def plot_tree_progress(snapshots, path: Path) -> None:
    canvas = Image.new("RGB", (1800, 1100), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((30, 20), "Эволюция лучшего программного дерева", fill="black")
    for index, (generation, node) in enumerate(snapshots):
        x0 = 20 + (index % 3) * 590
        y0 = 70 + (index // 3) * 500
        draw.text((x0, y0), f"Поколение {generation}: {expression(node)}", fill="black")
        draw_tree(node, (draw, canvas), x0 + 280, y0 + 50, 150)
    canvas.save(path)


def plot_comparison(best, x_values, y_values, path: Path) -> None:
    grid = [-1.0 + 2.0 * i / 499 for i in range(500)]
    target = [target_function(float(x)) for x in grid]
    predicted = [evaluate(best, float(x)) for x in grid]
    canvas = Image.new("RGB", (1200, 650), "white")
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = 100, 70, 1130, 560
    draw.rectangle((left, top, right, bottom), outline="#444444", width=2)
    ymin = min(target + predicted) - 0.02
    ymax = max(target + predicted) + 0.02
    def point(x, y):
        return (left + (right-left) * (x + 1) / 2, bottom - (bottom-top) * (y-ymin)/(ymax-ymin))
    draw.line([point(x, y) for x, y in zip(grid, target)], fill="#c00000", width=4)
    draw.line([point(x, y) for x, y in zip(grid, predicted)], fill="#1f4e79", width=3)
    for x, y in zip(x_values, y_values):
        px, py = point(x, y)
        draw.ellipse((px-4, py-4, px+4, py+4), fill="#70ad47")
    draw.text((left, 20), "Сравнение исходной и найденной функций", fill="black")
    draw.text((left, 580), "x", fill="black")
    draw.text((10, top), "f(x)", fill="black")
    draw.line((850, 35, 880, 35), fill="#c00000", width=4)
    draw.text((890, 27), "исходная", fill="black")
    draw.line((850, 55, 880, 55), fill="#1f4e79", width=3)
    draw.text((890, 47), "найденная", fill="black")
    canvas.save(path)


def main() -> None:
    x_values, y_values = make_training_data()
    configs = {
        "baseline": dict(population_size=500, generations=150, max_depth=7, crossover_rate=0.85, mutation_rate=0.12),
        "population_250": dict(population_size=250, generations=150, max_depth=7, crossover_rate=0.85, mutation_rate=0.12),
        "population_750": dict(population_size=750, generations=150, max_depth=7, crossover_rate=0.85, mutation_rate=0.12),
        "crossover_0.60": dict(population_size=500, generations=150, max_depth=7, crossover_rate=0.60, mutation_rate=0.12),
        "crossover_1.00": dict(population_size=500, generations=150, max_depth=7, crossover_rate=1.00, mutation_rate=0.12),
        "mutation_0.05": dict(population_size=500, generations=150, max_depth=7, crossover_rate=0.85, mutation_rate=0.05),
        "mutation_0.25": dict(population_size=500, generations=150, max_depth=7, crossover_rate=0.85, mutation_rate=0.25),
    }
    summaries = {}
    baseline = None
    study_rows = []
    for index, (label, params) in enumerate(configs.items()):
        started = time.perf_counter()
        gp = GeneticProgramming(x_values, y_values, seed=4 + index, **params)
        best, mse = gp.run()
        elapsed = time.perf_counter() - started
        result = {
            "label": label,
            "mse": mse,
            "rmse": mse**0.5,
            "size": best.size(),
            "depth": best.depth(),
            "formula": expression(best),
            "elapsed_seconds": elapsed,
            "parameters": params | {"seed": 4 + index, "tournament_size": 5, "parsimony": 1e-5},
        }
        summaries[label] = result
        if label == "baseline":
            baseline = (gp, best, result)
        if label != "baseline":
            factor, value = label.rsplit("_", 1)
            study_rows.append({"factor": factor, "value": value, "mse": f"{mse:.10g}", "rmse": f"{mse**0.5:.10g}", "size": best.size(), "time_seconds": f"{elapsed:.3f}"})

    assert baseline is not None
    gp, best, base_result = baseline
    plot_convergence(gp.history, RESULTS / "convergence.png")
    plot_comparison(best, x_values, y_values, RESULTS / "function_comparison.png")
    plot_tree_progress(gp.snapshots, RESULTS / "tree_progress.png")
    for generation, node in gp.all_snapshots:
        plot_tree(node, generation, RESULTS / f"tree_generation_{generation:03d}.png")
    with (RESULTS / "training_data.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["x", "y"])
        writer.writerows(zip(x_values, y_values))
    write_csv(RESULTS / "parameter_study.csv", study_rows)
    summary = {
        "variant": 4,
        "target_formula": "f(x) = x^6 - 2*x^4 + x^2",
        "domain": "[-1, 1]",
        "points": 20,
        "terminal_set": ["x", "-5", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4", "5"],
        "function_set": ["+", "-", "*", "/", "protected pow", "abs", "sin", "cos", "exp", "sqrt", "pow2", "pow4", "pow6"],
        "problems": summaries,
        "baseline_history": gp.history,
    }
    (RESULTS / "results_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(base_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

