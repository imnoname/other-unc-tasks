"""Лабораторная работа 3 по МНК, вариант 20.

Исследуется ряд о числе женщин на 1000 мужчин в возрасте 20–24 лет
в Российской Федерации за 2012–2019 годы.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


YEARS = np.arange(2012, 2020, dtype=float)
VALUES = np.array([967, 966, 962, 959, 960, 960, 959, 961], dtype=float)
TRAIN_SIZE = len(YEARS) - 1
BASE_YEAR = int(YEARS[0])
VISUAL_POLYNOMIAL_DEGREE = 3


def manual_least_squares(x: np.ndarray, y: np.ndarray, degree: int = 2) -> np.ndarray:
    """Решает задачу МНК через нормальные уравнения.

    Коэффициенты возвращаются в возрастающем порядке: ``[a0, a1, ...]``.
    Функция намеренно не использует ``numpy.polyfit``.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y):
        raise ValueError("x и y должны быть одномерными массивами одинаковой длины")
    if degree < 0 or len(x) <= degree:
        raise ValueError("недостаточно наблюдений для заданной степени")

    design = np.column_stack([x**power for power in range(degree + 1)])
    normal_matrix = design.T @ design
    right_side = design.T @ y
    return np.linalg.solve(normal_matrix, right_side)


def predict_polynomial(x: np.ndarray, coefficients: np.ndarray) -> np.ndarray:
    """Вычисляет полином с коэффициентами в возрастающем порядке."""

    x = np.asarray(x, dtype=float)
    coefficients = np.asarray(coefficients, dtype=float)
    prediction = np.zeros_like(x, dtype=float)
    for power, coefficient in enumerate(coefficients):
        prediction += coefficient * x**power
    return prediction


def adjusted_r2(y_true: np.ndarray, y_pred: np.ndarray, parameter_count: int) -> float:
    """Возвращает скорректированный коэффициент детерминации.

    ``parameter_count`` — общее число оцениваемых параметров модели, включая
    свободный член. Такой вариант обозначений соответствует методичке.
    """

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if y_true.shape != y_pred.shape:
        raise ValueError("y_true и y_pred должны иметь одинаковую форму")
    n = y_true.size
    if n <= parameter_count:
        raise ValueError("для скорректированного R² недостаточно наблюдений")

    residual_sum = float(np.sum((y_true - y_pred) ** 2))
    total_sum = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if total_sum == 0:
        r2 = 1.0 if residual_sum == 0 else 0.0
    else:
        r2 = 1.0 - residual_sum / total_sum
    return float(1.0 - (1.0 - r2) * (n - 1) / (n - parameter_count))


def fit_functional_model(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    """Строит модель ``sqrt((x + 1) / 3) + C``.

    В качестве C берётся середина диапазона обучающих значений, как предложено
    в задании.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    constant = float((np.min(y) + np.max(y)) / 2.0)
    predictions = np.sqrt((x + 1.0) / 3.0) + constant
    return predictions, constant


def fit_library_polynomial(x: np.ndarray, y: np.ndarray, degree: int) -> tuple[np.ndarray, np.ndarray]:
    """Строит полином через ``numpy.polyfit`` и возвращает coeffs/predictions."""

    descending_coefficients = np.polyfit(x, y, degree)
    coefficients = descending_coefficients[::-1]
    return coefficients, predict_polynomial(x, coefficients)


def _metric_row(
    name: str,
    y_train: np.ndarray,
    y_pred: np.ndarray,
    parameter_count: int,
    *,
    degree: int | None = None,
    coefficients: np.ndarray | None = None,
    constant: float | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "name": name,
        "parameter_count": parameter_count,
        "r2_adjusted": adjusted_r2(y_train, y_pred, parameter_count),
    }
    if degree is not None:
        row["degree"] = degree
    if coefficients is not None:
        row["coefficients"] = np.asarray(coefficients, dtype=float)
    if constant is not None:
        row["constant"] = constant
    return row


def _format_coefficients(coefficients: np.ndarray) -> str:
    terms = []
    for power, coefficient in enumerate(coefficients):
        terms.append(f"a{power}={coefficient:.10f}")
    return ", ".join(terms)


def _write_results_text(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "Лабораторная работа 3. МНК, вариант 20",
        "Ряд: число женщин на 1000 мужчин в возрасте 20–24 лет, РФ",
        f"Данные: {', '.join(str(int(value)) for value in VALUES)}",
        f"Обучение: {int(YEARS[0])}–{int(YEARS[TRAIN_SIZE - 1])}; валидация: {result['validation_year']}",
        "",
            "Скорректированный коэффициент детерминации:",
    ]
    for model in result["plot_models"]:
        line = f"- {model['name']}: R2_adj={model['r2_adjusted']:.8f}"
        if "degree" in model:
            line += f", степень={model['degree']}"
        if "coefficients" in model:
            line += f", {_format_coefficients(model['coefficients'])}"
        if "constant" in model:
            line += f", C={model['constant']:.8f}"
        lines.append(line)

    lines.extend(
        [
            "",
            f"Визуально выбранная степень библиотечного полинома: p={result['selected_polynomial_degree']}",
            f"Лучшая модель: {result['selected_model']}",
            f"Прогноз на {result['validation_year']}: {result['validation']['selected_model_prediction']:.8f}",
            f"Фактическое значение: {result['validation']['actual']:.8f}",
            f"Абсолютная ошибка: {result['validation']['absolute_error']:.8f}",
            f"Относительная ошибка: {result['validation']['relative_error_percent']:.8f}%",
            f"Прогноз на {result['forecast_year']}: {result['forecast']['selected_model_prediction']:.8f}",
            f"Максимальная разница ручной и библиотечной квадратичных моделей: {result['manual_library_max_difference']:.12e}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_results_csv(path: Path, result: dict[str, Any]) -> None:
    fieldnames = [
        "model",
        "degree",
        "parameter_count",
        "r2_adjusted",
        "validation_prediction",
        "validation_absolute_error",
        "validation_relative_error_percent",
        "forecast_2020",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for model in result["models"]:
            prediction_2019 = float(model["predict"](result["validation_x"]))
            prediction_2020 = float(model["predict"](result["forecast_x"]))
            actual = float(result["validation"]["actual"])
            writer.writerow(
                {
                    "model": model["name"],
                    "degree": model.get("degree", ""),
                    "parameter_count": model["parameter_count"],
                    "r2_adjusted": f"{model['r2_adjusted']:.12f}",
                    "validation_prediction": f"{prediction_2019:.12f}",
                    "validation_absolute_error": f"{abs(prediction_2019 - actual):.12f}",
                    "validation_relative_error_percent": f"{abs(prediction_2019 - actual) / abs(actual) * 100:.12f}",
                    "forecast_2020": f"{prediction_2020:.12f}",
                }
            )


def _save_plot(path: Path, result: dict[str, Any]) -> None:
    x_plot = np.linspace(0.0, 8.0, 400)
    years_plot = BASE_YEAR + x_plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(YEARS[:TRAIN_SIZE], VALUES[:TRAIN_SIZE], color="black", marker="o", label="Обучающие данные")
    ax.scatter(
        YEARS[TRAIN_SIZE],
        VALUES[TRAIN_SIZE],
        color="red",
        marker="x",
        s=80,
        label="Валидационная точка 2019",
    )
    for model in result["plot_models"]:
        ax.plot(years_plot, model["predict"](x_plot), linewidth=1.8, label=model["plot_label"])
    ax.set_title("ЛР-3 МНК, вариант 20")
    ax.set_xlabel("Год")
    ax.set_ylabel("Женщин на 1000 мужчин")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run_analysis(output_dir: str | Path | None = None) -> dict[str, Any]:
    """Выполняет все пункты расчёта и сохраняет артефакты лабораторной."""

    output_path = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parent
    output_path.mkdir(parents=True, exist_ok=True)

    x = YEARS - BASE_YEAR
    train_x = x[:TRAIN_SIZE]
    train_y = VALUES[:TRAIN_SIZE]
    validation_x = float(x[TRAIN_SIZE])
    validation_year = int(YEARS[TRAIN_SIZE])
    forecast_x = validation_x + 1.0
    forecast_year = validation_year + 1

    manual_coefficients = manual_least_squares(train_x, train_y, degree=2)
    manual_model = {
        **_metric_row(
            "manual_quadratic",
            train_y,
            predict_polynomial(train_x, manual_coefficients),
            parameter_count=3,
            degree=2,
            coefficients=manual_coefficients,
        ),
        "predict": lambda values, c=manual_coefficients: predict_polynomial(values, c),
        "plot_label": "Ручной МНК, p=2",
    }

    library_quadratic_coefficients, library_quadratic_train = fit_library_polynomial(train_x, train_y, 2)
    library_quadratic = {
        **_metric_row(
            "library_quadratic",
            train_y,
            library_quadratic_train,
            parameter_count=3,
            degree=2,
            coefficients=library_quadratic_coefficients,
        ),
        "predict": lambda values, c=library_quadratic_coefficients: predict_polynomial(values, c),
        "plot_label": "numpy.polyfit, p=2",
    }

    candidate_models: list[dict[str, Any]] = []
    for degree in (1, 3, 4, 5):
        coefficients, predictions = fit_library_polynomial(train_x, train_y, degree)
        candidate_models.append(
            {
                **_metric_row(
                    f"polynomial_degree_{degree}",
                    train_y,
                    predictions,
                    parameter_count=degree + 1,
                    degree=degree,
                    coefficients=coefficients,
                ),
                "predict": lambda values, c=coefficients: predict_polynomial(values, c),
                "plot_label": f"numpy.polyfit, p={degree}",
            }
        )

    # По пункту b степень выбирается визуально. Для этого ряда p=3 даёт
    # спокойную кривую без заметного выброса и почти совпадает с p=2.
    best_polynomial = next(
        model for model in candidate_models if model["degree"] == VISUAL_POLYNOMIAL_DEGREE
    )
    functional_train, functional_constant = fit_functional_model(train_x, train_y)
    functional_model = {
        **_metric_row(
            "functional",
            train_y,
            functional_train,
            parameter_count=1,
            constant=functional_constant,
        ),
        "predict": lambda values, c=functional_constant: np.sqrt((np.asarray(values, dtype=float) + 1.0) / 3.0) + c,
        "plot_label": "Функциональная модель",
    }

    comparison_models = [manual_model, best_polynomial, functional_model]
    selected_model = max(comparison_models, key=lambda model: model["r2_adjusted"])
    selected_model_key = "best_polynomial" if selected_model is best_polynomial else selected_model["name"]
    selected_validation_prediction = float(selected_model["predict"](validation_x))
    actual = float(VALUES[TRAIN_SIZE])
    absolute_error = abs(selected_validation_prediction - actual)
    relative_error = absolute_error / abs(actual) * 100.0

    output_paths = {
        "plot": output_path / "lab3_mnk_variant20_plot.png",
        "text": output_path / "lab3_mnk_variant20_results.txt",
        "csv": output_path / "lab3_mnk_variant20_results.csv",
    }
    result: dict[str, Any] = {
        "training_years": YEARS[:TRAIN_SIZE].astype(int).tolist(),
        "validation_year": validation_year,
        "forecast_year": forecast_year,
        "validation_x": validation_x,
        "forecast_x": forecast_x,
        "models": comparison_models,
        "all_polynomial_candidates": candidate_models,
        "plot_models": [manual_model, *candidate_models, functional_model],
        "selected_polynomial_degree": VISUAL_POLYNOMIAL_DEGREE,
        "selected_model": selected_model_key,
        "validation": {
            "actual": actual,
            "selected_model_prediction": selected_validation_prediction,
            "absolute_error": absolute_error,
            "relative_error_percent": relative_error,
        },
        "forecast": {
            "selected_model_prediction": float(selected_model["predict"](forecast_x)),
        },
        "manual_library_max_difference": float(
            np.max(np.abs(predict_polynomial(train_x, manual_coefficients) - library_quadratic_train))
        ),
        "output_paths": output_paths,
    }
    _save_plot(output_paths["plot"], result)
    _write_results_text(output_paths["text"], result)
    _write_results_csv(output_paths["csv"], result)
    return result


def main() -> None:
    result = run_analysis()
    print("Лабораторная работа 3, вариант 20")
    print(f"Визуально выбранная степень полинома: p={result['selected_polynomial_degree']}")
    print(f"Лучшая модель: {result['selected_model']}")
    print(f"Прогноз на {result['validation_year']}: {result['validation']['selected_model_prediction']:.6f}")
    print(f"Абсолютная ошибка валидации: {result['validation']['absolute_error']:.6f}")
    print(f"Относительная ошибка валидации: {result['validation']['relative_error_percent']:.6f}%")
    print(f"Прогноз на {result['forecast_year']}: {result['forecast']['selected_model_prediction']:.6f}")
    print("Файлы результатов сохранены рядом со скриптом.")


if __name__ == "__main__":
    main()

