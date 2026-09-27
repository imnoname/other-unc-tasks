"""File-based emulator of a one-tape deterministic Turing machine.

The command format is:
    q_i read -> q_k write direction

The blank symbol is written as the Greek lambda (λ) in the input files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import TextIO


BLANK = "λ"
HALT_STATE = "qz"
COMMAND_RE = re.compile(
    r"^(?P<state>\S+)\s+(?P<read>\S+)\s*->\s*"
    r"(?P<next_state>\S+)\s+(?P<write>\S+)\s+(?P<direction>[RLE])$"
)


class MachineError(RuntimeError):
    """An invalid machine description or an execution error."""


@dataclass(frozen=True)
class Command:
    state: str
    read: str
    next_state: str
    write: str
    direction: str


@dataclass(frozen=True)
class TraceEntry:
    step: int
    state: str
    head: int
    tape: str
    command: str


@dataclass(frozen=True)
class MachineResult:
    final_state: str
    steps: int
    final_tape: str
    result: str
    trace: tuple[TraceEntry, ...]


def _read_utf8(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def load_alphabet(path: str | Path) -> set[str]:
    symbols = _read_utf8(path).split()
    if not symbols:
        raise MachineError("Внешний алфавит пуст")
    if any(len(symbol) != 1 for symbol in symbols):
        raise MachineError("Каждый символ внешнего алфавита должен занимать один знак")
    if BLANK not in symbols:
        raise MachineError("Во внешнем алфавите отсутствует пустой символ λ")
    return set(symbols)


def load_program(path: str | Path, alphabet: set[str]) -> dict[tuple[str, str], Command]:
    commands: dict[tuple[str, str], Command] = {}
    for line_number, raw_line in enumerate(_read_utf8(path).splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = COMMAND_RE.fullmatch(line)
        if not match:
            raise MachineError(f"Некорректная команда в строке {line_number}: {line}")
        data = match.groupdict()
        command = Command(
            state=data["state"],
            read=data["read"],
            next_state=data["next_state"],
            write=data["write"],
            direction=data["direction"],
        )
        if command.read not in alphabet or command.write not in alphabet:
            raise MachineError(
                f"Символ команды в строке {line_number} отсутствует во внешнем алфавите"
            )
        key = (command.state, command.read)
        if key in commands:
            raise MachineError(f"Дублирующийся переход в строке {line_number}")
        commands[key] = command
    if not commands:
        raise MachineError("Программа машины Тьюринга пуста")
    return commands


def load_tape(path: str | Path, alphabet: set[str]) -> str:
    tape = _read_utf8(path).strip()
    if not tape:
        raise MachineError("Входная лента пуста")
    missing = sorted(set(tape) - alphabet)
    if missing:
        raise MachineError(
            f"Символ(ы) {', '.join(missing)} отсутствует во внешнем алфавите"
        )
    return tape


def _tape_view(cells: dict[int, str], head: int, *, padding: int = 1) -> str:
    nonblank = [position for position, symbol in cells.items() if symbol != BLANK]
    left = min([head, *nonblank]) - padding
    right = max([head, *nonblank]) + padding
    return "".join(cells.get(position, BLANK) for position in range(left, right + 1))


def _format_command(command: Command | None) -> str:
    if command is None:
        return "нет команды"
    return (
        f"{command.state} {command.read} -> {command.next_state} "
        f"{command.write} {command.direction}"
    )


def _write_trace(stream: TextIO, result: MachineResult) -> None:
    stream.write("Эмулятор машины Тьюринга, вариант 20\n")
    stream.write("Функция: f(x,y) = (x + 1)(y + 1)\n\n")
    for entry in result.trace:
        stream.write(f"Шаг {entry.step}: состояние {entry.state}, позиция {entry.head}\n")
        stream.write(f"Лента: {entry.tape}\n")
        stream.write(f"Команда: {entry.command}\n\n")
    stream.write(f"Конечное состояние: {result.final_state}\n")
    stream.write(f"Число шагов: {result.steps}\n")
    stream.write(f"Финальная лента: {result.final_tape}\n")
    stream.write(f"Результат: {result.result}\n")


def run_machine(
    program_path: str | Path,
    alphabet_path: str | Path,
    tape_path: str | Path,
    output_path: str | Path | None,
    *,
    max_steps: int = 100_000,
) -> MachineResult:
    alphabet = load_alphabet(alphabet_path)
    program = load_program(program_path, alphabet)
    initial_tape = load_tape(tape_path, alphabet)

    cells = {position: symbol for position, symbol in enumerate(initial_tape)}
    state = "q0"
    head = 0
    trace: list[TraceEntry] = []

    for step in range(1, max_steps + 1):
        if state == HALT_STATE:
            break
        read = cells.get(head, BLANK)
        command = program.get((state, read))
        if command is None:
            raise MachineError(
                f"Не задан переход для состояния {state} и символа {read} "
                f"на шаге {step}"
            )
        trace.append(
            TraceEntry(
                step=step,
                state=state,
                head=head,
                tape=_tape_view(cells, head),
                command=_format_command(command),
            )
        )
        cells[head] = command.write
        if command.direction == "R":
            head += 1
        elif command.direction == "L":
            head -= 1
        state = command.next_state
    else:
        raise MachineError(f"Превышено максимальное число шагов: {max_steps}")

    if state != HALT_STATE:
        raise MachineError("Машина завершилась без перехода в конечное состояние qz")

    final_tape = _tape_view(cells, head, padding=0)
    result_marker = "="
    marker_positions = [position for position, symbol in cells.items() if symbol == result_marker]
    if not marker_positions:
        raise MachineError("На финальной ленте отсутствует разделитель результата =")
    marker = max(marker_positions)
    result_chars: list[str] = []
    position = marker + 1
    while cells.get(position, BLANK) == "1":
        result_chars.append("1")
        position += 1
    result = "".join(result_chars)

    machine_result = MachineResult(
        final_state=state,
        steps=len(trace),
        final_tape=final_tape,
        result=result,
        trace=tuple(trace),
    )
    if output_path is not None:
        with Path(output_path).open("w", encoding="utf-8") as stream:
            _write_trace(stream, machine_result)
    return machine_result


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", required=True, help="Файл команд МТ")
    parser.add_argument("--alphabet", required=True, help="Файл внешнего алфавита")
    parser.add_argument("--tape", required=True, help="Файл входной ленты")
    parser.add_argument("--output", required=True, help="Файл результата и трассировки")
    parser.add_argument("--max-steps", type=int, default=100_000)
    args = parser.parse_args()

    try:
        result = run_machine(
            args.program,
            args.alphabet,
            args.tape,
            args.output,
            max_steps=args.max_steps,
        )
    except (OSError, MachineError) as error:
        parser.error(str(error))
    print(f"Конечное состояние: {result.final_state}")
    print(f"Шагов: {result.steps}")
    print(f"Результат: {result.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
