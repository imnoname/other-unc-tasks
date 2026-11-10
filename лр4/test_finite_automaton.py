import pytest

from finite_automaton import REPRESENTATIONS, main, run_word


@pytest.mark.parametrize("word", ["a", "ab", "acdeee"])
def test_accepts_words_from_variant20_language(word):
    for representation in REPRESENTATIONS:
        result = run_word(word, representation)
        assert result["accepted"] is True
        assert result["error"] is None


@pytest.mark.parametrize("word", ["", "ba", "acb", "aeb", "af"])
def test_rejects_words_outside_variant20_language(word):
    for representation in REPRESENTATIONS:
        result = run_word(word, representation)
        assert result["accepted"] is False
        assert result["error"]


def test_three_representations_produce_same_trace_and_decision():
    for word in ("a", "abbb", "acdeee", "ba", "acb", "aeb", "af", ""):
        results = [run_word(word, representation) for representation in REPRESENTATIONS]
        comparable = [
            {key: value for key, value in result.items() if key != "representation"}
            for result in results
        ]
        assert comparable[0] == comparable[1] == comparable[2]


def test_run_word_returns_exact_trace_for_nullable_suffix():
    result = run_word("a", "table")
    assert result["states"] == ["q0", "q1"]
    assert result["outputs"] == ["0"]
    assert result["accepted"] is True


def test_cli_prints_each_representation(capsys):
    exit_code = main(["acb"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.count("Представление:") == 3
    assert output.count("Недопустимо") == 3
    assert "q0 -> q1 -> q2" in output
    assert "a(b)*(c|d)*(e)*" in output


def test_cli_requires_one_word(capsys):
    exit_code = main([])
    output = capsys.readouterr().out
    assert exit_code == 2
    assert "Укажите слово" in output
