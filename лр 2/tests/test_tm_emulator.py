import pytest

from tm_emulator import MachineError, run_machine


def test_variant20_returns_nine_unary_ones_for_two_by_two_input():
    result = run_machine(
        program_path="data/variant20.tm",
        alphabet_path="data/alphabet.txt",
        tape_path="data/tape_2x2.txt",
        output_path=None,
    )

    assert result.final_state == "qz"
    assert result.result == "111111111"
    assert result.steps > 0


def test_variant20_handles_zero_arguments_after_increment():
    result = run_machine(
        program_path="data/variant20.tm",
        alphabet_path="data/alphabet.txt",
        tape_path="data/tape_0x0.txt",
        output_path=None,
    )

    assert result.final_state == "qz"
    assert result.result == "1"


def test_machine_reports_missing_transition(tmp_path):
    program = tmp_path / "program.tm"
    alphabet = tmp_path / "alphabet.txt"
    tape = tmp_path / "tape.txt"
    program.write_text("q0 1 -> q1 1 E\n", encoding="utf-8")
    alphabet.write_text("1 λ\n", encoding="utf-8")
    tape.write_text("11", encoding="utf-8")

    with pytest.raises(MachineError, match="Не задан переход"):
        run_machine(str(program), str(alphabet), str(tape), None)


def test_machine_reports_symbol_outside_alphabet(tmp_path):
    program = tmp_path / "program.tm"
    alphabet = tmp_path / "alphabet.txt"
    tape = tmp_path / "tape.txt"
    program.write_text("q0 1 -> qz 1 E\n", encoding="utf-8")
    alphabet.write_text("1 λ\n", encoding="utf-8")
    tape.write_text("1*1", encoding="utf-8")

    with pytest.raises(MachineError, match="отсутствует во внешнем алфавите"):
        run_machine(str(program), str(alphabet), str(tape), None)
