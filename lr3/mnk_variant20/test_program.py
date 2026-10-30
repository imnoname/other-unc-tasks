import numpy as np
import pytest

from program import (
    TRAIN_SIZE,
    VALUES,
    YEARS,
    adjusted_r2,
    fit_functional_model,
    manual_least_squares,
    predict_polynomial,
    run_analysis,
)


def test_variant20_data_has_training_and_validation_points():
    assert len(YEARS) == 8
    assert len(VALUES) == 8
    assert TRAIN_SIZE == 7
    assert YEARS[TRAIN_SIZE] == 2019


def test_manual_least_squares_returns_ascending_quadratic_coefficients():
    x = np.arange(4, dtype=float)
    y = 2.0 + 3.0 * x + 4.0 * x**2

    coefficients = manual_least_squares(x, y, degree=2)

    np.testing.assert_allclose(coefficients, [2.0, 3.0, 4.0], atol=1e-12)
    np.testing.assert_allclose(predict_polynomial(x, coefficients), y, atol=1e-12)


def test_adjusted_r2_is_one_for_a_perfect_fit():
    y = np.array([1.0, 2.0, 4.0, 8.0])

    assert adjusted_r2(y, y, parameter_count=1) == 1.0


def test_adjusted_r2_uses_total_parameter_count_formula():
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.0, 2.0, 2.0, 4.0, 6.0])

    # R² = 1 - 2 / 10 = 0.8; k=2, n=5.
    expected = 1.0 - (1.0 - 0.8) * (5 - 1) / (5 - 2)
    assert adjusted_r2(y, y_pred, parameter_count=2) == expected


def test_variant_manual_quadratic_matches_numpy_polyfit():
    x = YEARS[:TRAIN_SIZE] - YEARS[0]
    y = VALUES[:TRAIN_SIZE]

    manual = manual_least_squares(x, y, degree=2)
    library = np.polyfit(x, y, 2)[::-1]

    np.testing.assert_allclose(manual, library, atol=1e-10)


def test_functional_model_is_finite_and_uses_source_level():
    x = np.arange(7, dtype=float)
    y = VALUES[:TRAIN_SIZE]

    predictions, constant = fit_functional_model(x, y)

    assert np.isfinite(predictions).all()
    assert constant == (np.min(y) + np.max(y)) / 2


def test_analysis_keeps_2019_for_validation_and_forecasts_2020(tmp_path):
    result = run_analysis(tmp_path)

    assert result["training_years"][-1] == 2018
    assert result["validation_year"] == 2019
    assert result["forecast_year"] == 2020
    assert result["selected_polynomial_degree"] == 3
    assert result["selected_model"] in {"manual_quadratic", "best_polynomial", "functional"}
    assert result["selected_model"] == "manual_quadratic"
    assert result["validation"]["selected_model_prediction"] == pytest.approx(960.4285714286)
    assert result["forecast"]["selected_model_prediction"] == pytest.approx(962.0714285714)
    assert np.isfinite(result["validation"]["selected_model_prediction"])
    assert np.isfinite(result["forecast"]["selected_model_prediction"])


def test_analysis_writes_plot_text_and_csv(tmp_path):
    result = run_analysis(tmp_path)

    assert {model["degree"] for model in result["plot_models"] if "degree" in model} == {1, 2, 3, 4, 5}
    for path in result["output_paths"].values():
        assert path.exists()
        assert path.stat().st_size > 0

