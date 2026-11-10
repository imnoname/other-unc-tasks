"""CLI-распознаватель автомата Мили, лабораторная работа № 4, вариант 20."""

from __future__ import annotations

import sys


STATES = ("q0", "q1", "q2", "q3")
INPUT_ALPHABET = frozenset("abcde")
OUTPUT_ALPHABET = frozenset("01")
INITIAL_STATE = "q0"
ACCEPTING_STATES = frozenset({"q1", "q2", "q3"})
REPRESENTATIONS = ("table", "graph", "matrix")

# Способ 1: таблицы переходов δ и выходов λ.
TABLE_TRANSITIONS = {
    ("q0", "a"): "q1",
    ("q1", "b"): "q1",
    ("q1", "c"): "q2",
    ("q1", "d"): "q2",
    ("q1", "e"): "q3",
    ("q2", "c"): "q2",
    ("q2", "d"): "q2",
    ("q2", "e"): "q3",
    ("q3", "e"): "q3",
}
TABLE_OUTPUTS = {
    (state, symbol): ("1" if symbol == "e" else "0")
    for state, symbol in TABLE_TRANSITIONS
}

# Способ 2: ориентированный граф с метками дугами (вход, выход).
GRAPH = {
    "q0": {"a": ("q1", "0")},
    "q1": {"b": ("q1", "0"), "c": ("q2", "0"), "d": ("q2", "0"), "e": ("q3", "1")},
    "q2": {"c": ("q2", "0"), "d": ("q2", "0"), "e": ("q3", "1")},
    "q3": {"e": ("q3", "1")},
}

# Способ 3: матрица переходов-выходов; для пары состояний записаны (вход, выход).
MATRIX = {
    ("q0", "q1"): {"a": "0"},
    ("q1", "q1"): {"b": "0"},
    ("q1", "q2"): {"c": "0", "d": "0"},
    ("q1", "q3"): {"e": "1"},
    ("q2", "q2"): {"c": "0", "d": "0"},
    ("q2", "q3"): {"e": "1"},
    ("q3", "q3"): {"e": "1"},
}

REPRESENTATION_NAMES = {
    "table": "Таблицы переходов и выходов",
    "graph": "Ориентированный граф",
    "matrix": "Матрица переходов-выходов",
}


def _step(state: str, symbol: str, representation: str) -> tuple[str, str] | None:
    if representation == "table":
        destination = TABLE_TRANSITIONS.get((state, symbol))
        if destination is None:
            return None
        return destination, TABLE_OUTPUTS[(state, symbol)]
    if representation == "graph":
        return GRAPH.get(state, {}).get(symbol)
    if representation == "matrix":
        for (origin, destination), symbols in MATRIX.items():
            if origin == state and symbol in symbols:
                return destination, symbols[symbol]
        return None
    raise ValueError(f"Неизвестное представление: {representation}")


def run_word(word: str, representation: str) -> dict:
    """Выполняет один вход по выбранной форме автомата и возвращает протокол."""
    if representation not in REPRESENTATIONS:
        raise ValueError(f"Представление должно быть одним из: {', '.join(REPRESENTATIONS)}")

    state = INITIAL_STATE
    states = [state]
    outputs: list[str] = []
    error = None

    for symbol in word:
        if symbol not in INPUT_ALPHABET:
            error = f"Неизвестный входной символ {symbol!r} (символ вне X)"
            break
        transition = _step(state, symbol, representation)
        if transition is None:
            error = f"Нет перехода из {state} по символу {symbol!r}"
            break
        state, output = transition
        states.append(state)
        outputs.append(output)

    accepted = error is None and state in ACCEPTING_STATES and len(states) == len(word) + 1
    if error is None and not accepted:
        error = f"Слово закончилось в недопускающем состоянии {state}"

    return {
        "word": word,
        "representation": representation,
        "states": states,
        "outputs": outputs,
        "accepted": accepted,
        "error": error,
    }


def _format_result(result: dict) -> str:
    states = " -> ".join(result["states"])
    outputs = ", ".join(result["outputs"]) if result["outputs"] else "—"
    status = "Допустимо" if result["accepted"] else "Недопустимо"
    lines = [
        f"Представление: {REPRESENTATION_NAMES[result['representation']]}",
        f"Слово: {result['word'] if result['word'] else '(пустое слово)'}",
        f"Траектория: {states}",
        f"Выходы: {outputs}",
        f"Результат: {status}",
    ]
    if result["error"]:
        lines.append(f"Причина: {result['error']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Укажите слово одним аргументом: python finite_automaton.py <слово>")
        return 2

    word = args[0]
    print("Регулярное выражение варианта 20: a(b)*(c|d)*(e)*")
    print(f"Проверяемое слово: {word if word else '(пустое слово)'}")
    print(f"Допускающие состояния: {', '.join(sorted(ACCEPTING_STATES))}\n")
    for index, representation in enumerate(REPRESENTATIONS):
        print(_format_result(run_word(word, representation)))
        if index != len(REPRESENTATIONS) - 1:
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
