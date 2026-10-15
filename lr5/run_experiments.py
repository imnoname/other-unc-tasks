"""Run reproducible evolution-strategy experiments and create figures."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from evolution_strategy import EvolutionStrategy, Individual, objective


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"


def font(size: int):
    return ImageFont.truetype(FONT_PATH, size)


def color(value: float, maximum: float) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, value / max(maximum, 1e-12)))
    return (int(245 * ratio), int(80 + 140 * (1 - ratio)), int(210 * (1 - ratio)))


def map_xy(x: float, y: float, bounds: tuple[float, float], box: tuple[int, int, int, int]) -> tuple[float, float]:
    left, top, right, bottom = box
    lo, hi = bounds
    return left + (x - lo) / (hi - lo) * (right - left), bottom - (y - lo) / (hi - lo) * (bottom - top)


def plot_population(result, path: Path) -> None:
    """Draw a contour-like view for n=2 and the final population."""
    canvas = Image.new("RGB", (1200, 760), "white")
    draw = ImageDraw.Draw(canvas)
    box = (100, 80, 1080, 650)
    lo, hi = -5.12, 5.12
    grid = 70
    max_value = objective([hi, hi])
    for row in range(grid):
        for col in range(grid):
            x = lo + (hi - lo) * (col + 0.5) / grid
            y = lo + (hi - lo) * (row + 0.5) / grid
            px = int(box[0] + col * (box[2] - box[0]) / grid)
            py = int(box[1] + (grid - 1 - row) * (box[3] - box[1]) / grid)
            cw = int((box[2] - box[0]) / grid) + 1
            ch = int((box[3] - box[1]) / grid) + 1
            draw.rectangle((px, py, px + cw, py + ch), fill=color(objective([x, y]), max_value))
    draw.rectangle(box, outline="black", width=2)
    draw.line((box[0], (box[1] + box[3]) / 2, box[2], (box[1] + box[3]) / 2), fill="#777777", width=1)
    draw.line(((box[0] + box[2]) / 2, box[1], (box[0] + box[2]) / 2, box[3]), fill="#777777", width=1)
    final_population = result.snapshots[-1]
    for item in final_population:
        px, py = map_xy(item.x[0], item.x[1], (lo, hi), box)
        draw.ellipse((px - 6, py - 6, px + 6, py + 6), fill="#1677b5", outline="white")
    best_x, best_y = map_xy(result.best.x[0], result.best.x[1], (lo, hi), box)
    draw.ellipse((best_x - 10, best_y - 10, best_x + 10, best_y + 10), outline="#008000", width=3)
    draw.text((35, 25), f"Вариант 4, n=2; найденный минимум f={result.best.value:.6g}", fill="black", font=font(22))
    draw.text((box[0], 680), "x1", fill="black", font=font(18))
    draw.text((25, box[1]), "x2", fill="black", font=font(18))
    draw.text((800, 25), "синие точки - популяция; зеленая окружность - лучший результат", fill="black", font=font(16))
    canvas.save(path)


def plot_convergence(results: dict[int, object], path: Path) -> None:
    canvas = Image.new("RGB", (1200, 650), "white")
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = 110, 70, 1120, 540
    draw.rectangle((left, top, right, bottom), outline="black", width=2)
    colors = {2: "#b2182b", 3: "#2166ac"}
    max_gen = max(max(item["generation"] for item in result.history) for result in results.values())
    max_log = max(math.log10(max(item["best_value"] for item in result.history) + 1e-8) for result in results.values())
    min_log = min(math.log10(max(item["best_value"], 1e-12)) for result in results.values() for item in result.history)
    if max_log <= min_log:
        max_log = min_log + 1
    for n, result in results.items():
        points = []
        for item in result.history:
            px = left + (right - left) * item["generation"] / max(1, max_gen)
            py = bottom - (bottom - top) * (math.log10(max(item["best_value"], 1e-12)) - min_log) / (max_log - min_log)
            points.append((px, py))
        draw.line(points, fill=colors[n], width=4)
        draw.text((900, 20 + (n - 2) * 25), f"n={n}", fill=colors[n], font=font(18))
    draw.text((left, 20), "Сходимость ES (log10 от значения функции)", fill="black", font=font(22))
    draw.text((left, 570), "поколение", fill="black", font=font(18))
    canvas.save(path)


def plot_parameter_study(rows: list[dict], path: Path) -> None:
    canvas = Image.new("RGB", (1200, 700), "white")
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = 100, 80, 1100, 580
    draw.rectangle((left, top, right, bottom), outline="black", width=2)
    values = [max(float(row["best_value"]), 1e-14) for row in rows]
    logs = [math.log10(value) for value in values]
    low, high = min(logs), max(logs)
    if high - low < 1e-9:
        high = low + 1
    for i, row in enumerate(rows):
        x = left + (right-left) * (i + 0.5) / len(rows)
        log_value = math.log10(max(float(row["best_value"]), 1e-14))
        bar_top = bottom - (bottom-top) * (log_value-low)/(high-low)
        draw.rectangle((x-28, bar_top, x+28, bottom), fill="#4f81bd")
        draw.text((x-23, bottom+8), str(row["label"]).replace("_", "\n"), fill="black", font=font(16))
        draw.text((x-23, bar_top-22), f"{float(row['best_value']):.1e}", fill="black", font=font(14))
    draw.text((left, 25), "Исследование параметров ES: log10 лучшего значения целевой функции", fill="black", font=font(22))
    canvas.save(path)


def main() -> None:
    base_results = {}
    for n in (2, 3):
        base_results[n] = EvolutionStrategy(n, population_size=20, mutation_probability=1.0, max_generations=100, seed=4 + n).run()
    plot_population(base_results[2], RESULTS / "population_n2.png")
    plot_convergence(base_results, RESULTS / "convergence_n2_n3.png")
    for index, population in enumerate(base_results[2].snapshots):
        if index in {0, 5, 10}:
            snapshot_result = base_results[2]
            snapshot_result.snapshots = [population]
            plot_population(snapshot_result, RESULTS / f"step_n2_{index * 10:03d}.png")

    study_rows = []
    for population in (5, 10, 20, 40):
        result = EvolutionStrategy(2, population_size=population, mutation_probability=1.0, max_generations=100, seed=10 + population).run()
        study_rows.append({"factor": "population", "label": f"mu={population}", "value": population, "best_value": result.best.value, "generations": result.stopped_generation, "time_seconds": result.elapsed_seconds, "distance": math.sqrt(sum(value * value for value in result.best.x))})
    for probability in (0.25, 0.50, 0.75, 1.00):
        result = EvolutionStrategy(2, population_size=20, mutation_probability=probability, max_generations=100, seed=30 + int(probability * 100)).run()
        study_rows.append({"factor": "mutation_probability", "label": f"p={probability:.2f}", "value": probability, "best_value": result.best.value, "generations": result.stopped_generation, "time_seconds": result.elapsed_seconds, "distance": math.sqrt(sum(value * value for value in result.best.x))})
    with (RESULTS / "parameter_study.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(study_rows[0]))
        writer.writeheader(); writer.writerows(study_rows)
    plot_parameter_study(study_rows, RESULTS / "parameter_study.png")
    summary = {
        "variant": 4,
        "formula_printed": "f(x) = sum(5*i*x_i^2), i=1..n",
        "interpretation": "The printed formula is used literally; its mathematical minimum is x_i=0. The nearby table entry x_i=5*i is recorded as an inconsistency in the source guide.",
        "bounds": [-5.12, 5.12],
        "population_size": 20,
        "offspring_count": 20,
        "mutation_probability": 1.0,
        "max_generations": 100,
        "stagnation_limit": 25,
        "base": {
            str(n): {"best_value": result.best.value, "best_x": result.best.x, "distance": math.sqrt(sum(value * value for value in result.best.x)), "generations": result.stopped_generation, "time_seconds": result.elapsed_seconds, "history": result.history}
            for n, result in base_results.items()
        },
        "study": study_rows,
    }
    (RESULTS / "results_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"n2": summary["base"]["2"], "n3": summary["base"]["3"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

