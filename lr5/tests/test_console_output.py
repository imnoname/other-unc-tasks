from run_experiments import format_run_summary, selected_history_rows


def test_summary_shows_coordinates_and_convergence_metrics():
    result = {"dimension": 2, "best_value": 0.0001, "best_x": [0.01, -0.02],
              "generations": 80, "time_seconds": 0.25, "distance": 0.02236}
    text = format_run_summary(result)
    assert "n=2" in text
    assert "0.0001" in text
    assert "0.01" in text
    assert "80" in text


def test_selected_history_rows_includes_final_generation():
    history = [{"generation": i, "best_value": 1.0 / (i + 1)} for i in range(13)]
    assert [row["generation"] for row in selected_history_rows(history)] == [0, 10, 12]

