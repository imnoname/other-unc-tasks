import pytest

from posta_emulator import PostaError, run_system


BASE_CONFIG = """\
A = {1, /, =, P, Q, L, R};
X = {a, b, c};
A1 = {11/11=};
R = {
(1) a/b= -> Pa/Qb=;
(2) Pa/Qb= -> La1/Rb1=;
(3) La1/Rb=c -> La/Rb=cb;
(4) L/Rb=c -> =c;
}
"""


def write_config(tmp_path, content=BASE_CONFIG):
    path = tmp_path / "system.fs"
    path.write_text(content, encoding="utf-8")
    return path


def test_variant20_calculates_three_by_three(tmp_path):
    result = run_system(write_config(tmp_path), output_path=None)

    assert result.final_word == "=111111111"
    assert result.result == "111111111"
    assert result.steps == 6
    assert result.success is True


def test_variant20_calculates_another_unary_input(tmp_path):
    config = BASE_CONFIG.replace("A1 = {11/11=};", "A1 = {111/11=};")

    result = run_system(write_config(tmp_path, config), output_path=None)

    assert result.result == "111111111111"
    assert result.final_word == "=111111111111"


def test_emulator_rejects_symbol_outside_alphabet(tmp_path):
    config = BASE_CONFIG.replace("A1 = {11/11=};", "A1 = {11/21=};")

    with pytest.raises(PostaError, match="отсутствует во внешнем алфавите"):
        run_system(write_config(tmp_path, config), output_path=None)


def test_emulator_rejects_variable_outside_set(tmp_path):
    config = BASE_CONFIG.replace("La1/Rb=c", "Ld1/Rb=c")

    with pytest.raises(PostaError, match="Переменная 'd'"):
        run_system(write_config(tmp_path, config), output_path=None)
