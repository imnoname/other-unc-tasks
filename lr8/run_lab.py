"""Run the Lab 8 COCOMO parameter search and export reproducible results."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import random
import statistics
import sys
import time

from PIL import Image, ImageDraw, ImageFont

from cocomo_ga import FitResult, absolute_error_rms, fit_genetic_algorithm, predict

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "projects_18.csv"
RESULTS = ROOT / "results"
SPLIT_SEED = 3  # fixed split, leaves the unusually large source value visible in holdout


def load_data(path: Path = DATA) -> list[dict[str, float | int]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 18:
        raise ValueError(f"Expected 18 source projects, got {len(rows)}")
    return [{"id": int(r["project_id"]), "kloc": float(r["kloc"]), "effort": float(r["effort_person_months"])} for r in rows]


def split_data(rows: list[dict[str, float | int]], seed: int = SPLIT_SEED):
    indexes = list(range(len(rows)))
    random.Random(seed).shuffle(indexes)
    test_indexes = sorted(indexes[:5])
    train_indexes = sorted(indexes[5:])
    return [rows[i] for i in train_indexes], [rows[i] for i in test_indexes]


def metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("Metric vectors must have equal, non-zero lengths")
    errors = [abs(x - y) for x, y in zip(actual, predicted)]
    relative = [e / abs(x) for e, x in zip(errors, actual) if x != 0]
    return {
        "ED_RMS_person_months": absolute_error_rms(actual, predicted),
        "MD_sum_absolute_person_months": sum(errors),
        "MMRE_percent": 100.0 * statistics.mean(relative),
        "max_absolute_error_person_months": max(errors),
    }


def log_linear_baseline(train: list[dict[str, float | int]]):
    # Least-squares regression on ln(Ef) = ln(a) + b*ln(L); comparison only.
    xs = [math.log(float(r["kloc"])) for r in train]
    ys = [math.log(float(r["effort"])) for r in train]
    xm, ym = statistics.mean(xs), statistics.mean(ys)
    b = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / sum((x - xm) ** 2 for x in xs)
    a = math.exp(ym - b * xm)
    return a, b


def _font(size: int, bold: bool = False):
    paths = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf"),
    ]
    for path in paths:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _new_chart(title: str, subtitle: str, width: int = 1100, height: int = 650):
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 24), title, fill="#17243a", font=_font(28, True), anchor="ma")
    draw.text((width // 2, 64), subtitle, fill="#596579", font=_font(16), anchor="ma")
    return image, draw


def chart_convergence(history: tuple[float, ...], output: Path):
    image, draw = _new_chart("Сходимость генетического алгоритма", "Лучшее значение ED на обучающей выборке")
    x0, y0, x1, y1 = 100, 120, 1030, 550
    data = [max(v, 1e-9) for v in history]
    lo, hi = min(data), max(data)
    loglo, loghi = math.log10(lo), math.log10(hi)
    for k in range(5):
        y = y0 + k * (y1 - y0) / 4
        draw.line((x0, y, x1, y), fill="#e3e8ef", width=1)
        value = 10 ** (loghi - k * (loghi - loglo) / 4)
        draw.text((x0 - 12, y), f"{value:.2g}", fill="#596579", font=_font(14), anchor="rm")
    pts = []
    for i, value in enumerate(data):
        x = x0 + i * (x1 - x0) / max(1, len(data) - 1)
        y = y1 - (math.log10(value) - loglo) / max(1e-12, loghi - loglo) * (y1 - y0)
        pts.append((x, y))
    draw.line(pts, fill="#2768b2", width=4)
    for label, x, y in [("0", x0, y1 + 18), (str(len(data) - 1), x1, y1 + 18)]:
        draw.text((x, y), label, fill="#596579", font=_font(14), anchor="ma")
    draw.text((565, 610), "Поколение", fill="#27364b", font=_font(17), anchor="ma")
    image.save(output)


def chart_predictions(train, test, model_values, baseline_values, output: Path):
    image, draw = _new_chart("Фактические и прогнозные трудозатраты", "Логарифмические оси; заполненные маркеры — GA, контурные — регрессия")
    x0, y0, x1, y1 = 120, 130, 1015, 535
    actual = [float(r["effort"]) for r in train + test]
    all_values = actual + model_values + baseline_values
    lo = max(0.1, min(all_values) * 0.75)
    hi = max(all_values) * 1.15
    log_lo, log_hi = math.log10(lo), math.log10(hi)
    def sx(v): return x0 + (math.log10(max(lo, v))-log_lo)/(log_hi-log_lo)*(x1-x0)
    def sy(v): return y1 - (math.log10(max(lo, v))-log_lo)/(log_hi-log_lo)*(y1-y0)
    for k in range(6):
        value = 10 ** (log_lo + k*(log_hi-log_lo)/5)
        x, y = sx(value), sy(value)
        draw.line((x,y0,x,y1),fill="#e8edf3",width=1); draw.line((x0,y,x1,y),fill="#e8edf3",width=1)
        draw.text((x,y1+12),f"{value:.2g}",fill="#596579",font=_font(13),anchor="ma")
        draw.text((x0-10,y),f"{value:.2g}",fill="#596579",font=_font(13),anchor="rm")
    draw.line((sx(lo),sy(lo),sx(hi),sy(hi)),fill="#7e8999",width=2)
    all_rows=train+test
    for index,row in enumerate(all_rows):
        color="#2768b2" if index < len(train) else "#d77a24"
        x=sx(float(row["effort"]))
        for val,outline,offset in ((model_values[index],False,-4),(baseline_values[index],True,4)):
            y=sy(val)+offset
            draw.ellipse((x-6,y-6,x+6,y+6),fill="white" if outline else color,outline=color,width=2)
    draw.text((565,610),"Фактическое значение, чел.-мес.",fill="#27364b",font=_font(16),anchor="ma")
    draw.text((35,330),"Прогноз",fill="#27364b",font=_font(16),anchor="mm")
    draw.text((800,96),"Синее — обучение; оранжевое — тест",fill="#596579",font=_font(14))
    image.save(output)

def export_results(rows, train, test, result: FitResult, run_rows, baseline, elapsed: float):
    RESULTS.mkdir(exist_ok=True)
    a, b = result.a, result.b
    train_x = [float(r["kloc"]) for r in train]
    test_x = [float(r["kloc"]) for r in test]
    train_y = [float(r["effort"]) for r in train]
    test_y = [float(r["effort"]) for r in test]
    train_pred = predict(train_x, a, b)
    test_pred = predict(test_x, a, b)
    baseline_train = predict(train_x, *baseline)
    baseline_test = predict(test_x, *baseline)

    with (RESULTS / "ga_runs.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["seed", "a", "b", "train_ED"])
        writer.writeheader(); writer.writerows(run_rows)
    with (RESULTS / "predictions.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["project_id", "split", "kloc", "actual_effort", "ga_prediction", "ga_absolute_error", "ga_MRE_percent", "baseline_prediction"])
        for split, group, predictions, base_predictions in [("train", train, train_pred, baseline_train), ("test", test, test_pred, baseline_test)]:
            for r, p, bp in zip(group, predictions, base_predictions):
                actual = float(r["effort"])
                writer.writerow([r["id"], split, r["kloc"], actual, p, abs(actual-p), 100*abs(actual-p)/actual, bp])

    test_no_outlier = [(r, p) for r,p in zip(test,test_pred) if int(r["id"]) != 4]
    without_outlier = metrics([float(r["effort"]) for r,p in test_no_outlier],[p for r,p in test_no_outlier]) if test_no_outlier else None
    summary = {
        "model": "Ef = a * L^b",
        "fitness": "ED = sqrt(mean((actual - predicted)^2))",
        "split_seed": SPLIT_SEED,
        "training_project_ids": [int(r["id"]) for r in train],
        "test_project_ids": [int(r["id"]) for r in test],
        "source_anomaly_note": "Project 4 is preserved exactly as printed in the assignment: effort 909.8 person-months.",
        "ga": {"a": a, "b": b, "formula": f"Ef = {a:.6f} * L^{b:.6f}", "training_metrics": metrics(train_y,train_pred), "test_metrics": metrics(test_y,test_pred), "test_metrics_excluding_project_4": without_outlier, "generations": len(result.history)-1},
        "log_linear_baseline": {"a": baseline[0], "b": baseline[1], "training_metrics": metrics(train_y,baseline_train), "test_metrics": metrics(test_y,baseline_test)},
        "repeat_runs": run_rows,
        "elapsed_seconds": elapsed,
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    chart_convergence(result.history, RESULTS / "convergence.png")
    chart_predictions(train, test, train_pred+test_pred, baseline_train+baseline_test, RESULTS / "actual_vs_predicted.png")
    return summary


def run_experiment(runs: int = 8, verbose: bool = False):
    rows = load_data()
    train, test = split_data(rows)
    x = [float(r["kloc"]) for r in train]
    y = [float(r["effort"]) for r in train]
    run_rows = []
    best = None
    start = time.perf_counter()
    for run in range(runs):
        seed = 42 + run
        result = fit_genetic_algorithm(x, y, population_size=120, generations=600, crossover_probability=0.9, mutation_probability=0.15, seed=seed)
        record = {"seed": seed, "a": result.a, "b": result.b, "train_ED": result.error}
        run_rows.append(record)
        if best is None or result.error < best.error:
            best = result
        if verbose:
            print(f"Запуск {run+1:02d}/{runs}: a={result.a:.6f}, b={result.b:.6f}, ED train={result.error:.4f}")
    elapsed = time.perf_counter() - start
    baseline = log_linear_baseline(train)
    summary = export_results(rows, train, test, best, run_rows, baseline, elapsed)
    print("\nМодель COCOMO: Ef = a * L^b")
    print(f"Разбиение ({SPLIT_SEED=}): обучение {len(train)} проектов, тест {len(test)} проектов")
    print(f"GA: a={best.a:.6f}; b={best.b:.6f}; {summary['ga']['formula']}")
    print(f"ED обучения: {summary['ga']['training_metrics']['ED_RMS_person_months']:.3f} чел.-мес.")
    print(f"ED теста:    {summary['ga']['test_metrics']['ED_RMS_person_months']:.3f} чел.-мес.")
    print(f"Тест без проекта 4: {summary['ga']['test_metrics_excluding_project_4']['ED_RMS_person_months']:.3f} чел.-мес.")
    print(f"Лог-линейная база: a={baseline[0]:.6f}; b={baseline[1]:.6f}")
    print(f"Результаты и графики: {RESULTS}")
    return summary


def menu():
    print("Лабораторная работа 8. Генетическая настройка COCOMO")
    print("Вариант 4: вещественное кодирование, ED, арифметические операторы, рулетка")
    while True:
        print("\n1 — выполнить серию экспериментов\n2 — показать параметры метода\n0 — выход")
        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            run_experiment(verbose=True)
        elif choice == "2":
            print("Размер популяции: 120; поколения: 600; Pc=0.90; Pm=0.15; 8 независимых запусков.")
            print("Выбор: рулетка с преобразованием ошибки в положительные веса; сохранение элиты.")
        elif choice == "0":
            print("Работа завершена.")
            return
        else:
            print("Введите 1, 2 или 0.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Вариант 4: оценка параметров COCOMO генетическим алгоритмом")
    parser.add_argument("--run", action="store_true", help="выполнить эксперименты без диалогового меню")
    parser.add_argument("--runs", type=int, default=8, help="число независимых запусков GA")
    parser.add_argument("--verbose", action="store_true", help="показывать итоги каждого запуска")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be positive")
    run_experiment(args.runs, args.verbose) if args.run else menu()
