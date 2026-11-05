from run_experiments import format_run_summary, selected_history_rows


def test_summary_is_human_readable_and_contains_metrics():
    text = format_run_summary({
        "label": "baseline", "formula": "x + 1", "mse": 0.0123456,
        "rmse": 0.111111, "size": 3, "depth": 2, "elapsed_seconds": 1.25,
        "parameters": {"population_size": 50, "generations": 30, "crossover_rate": 0.8,
                       "mutation_rate": 0.1, "seed": 9},
    })
    assert "baseline" in text
    assert "0.0123456" in text
    assert "population_size=50" in text
    assert "x + 1" in text


def test_selected_history_rows_includes_start_milestones_and_end():
    history = [{"generation": i, "mse": 1.0 / (i + 1), "formula": f"x + {i}"} for i in range(31)]
    rows = selected_history_rows(history)
    assert [row["generation"] for row in rows] == [0, 10, 20, 30]

