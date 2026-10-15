"""Эмулятор канонической системы Поста для лабораторной работы № 3."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


class PostaError(ValueError):
    """Ошибка описания или выполнения формальной системы Поста."""


@dataclass(frozen=True)
class Rule:
    number: int
    lhs: str
    rhs: str

    @property
    def text(self) -> str:
        return f"({self.number}) {self.lhs} -> {self.rhs}"


@dataclass(frozen=True)
class TraceEntry:
    step: int
    before: str
    rule: Rule
    after: str


@dataclass(frozen=True)
class PostaResult:
    initial_word: str
    final_word: str
    result: str
    steps: int
    success: bool
    trace: tuple[TraceEntry, ...]


_SET_RE = re.compile(r"^\s*(A|X|A1)\s*=\s*\{(.*?)\}\s*;\s*$", re.DOTALL)
_RULE_RE = re.compile(
    r"^\s*\((\d+)\)\s*([^\s]+)\s*->\s*([^\s;]+)\s*;?\s*$"
)


def _parse_set(content: str, name: str) -> list[str]:
    match = _SET_RE.match(content)
    if not match or match.group(1) != name:
        raise PostaError(f"Не удалось разобрать множество {name}")
    values = [item.strip() for item in match.group(2).split(",") if item.strip()]
    if not values:
        raise PostaError(f"Множество {name} не должно быть пустым")
    return values


def parse_system(config_path: str | Path) -> tuple[set[str], set[str], str, list[Rule]]:
    """Разбирает текстовый файл описания системы Поста."""
    text = Path(config_path).read_text(encoding="utf-8")
    sections = re.split(r"\n\s*R\s*=\s*\{", text, maxsplit=1)
    if len(sections) != 2:
        raise PostaError("Отсутствует раздел R с продукциями")

    declarations = [line.strip() for line in sections[0].splitlines() if line.strip()]
    parsed: dict[str, list[str]] = {}
    for declaration in declarations:
        match = _SET_RE.match(declaration)
        if match:
            parsed[match.group(1)] = _parse_set(declaration, match.group(1))

    for name in ("A", "X", "A1"):
        if name not in parsed:
            raise PostaError(f"Отсутствует объявление {name}")

    rules_text = sections[1].rsplit("}", 1)[0]
    rules: list[Rule] = []
    for line in rules_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = _RULE_RE.match(line)
        if not match:
            raise PostaError(f"Некорректная продукция: {line}")
        rules.append(Rule(int(match.group(1)), match.group(2), match.group(3)))
    if not rules:
        raise PostaError("Множество продукций R не должно быть пустым")
    if len(parsed["A1"]) != 1:
        raise PostaError("Для запуска эмулятора требуется ровно одна аксиома A1")

    alphabet = set(parsed["A"])
    variables = set(parsed["X"])
    if any(len(symbol) != 1 for symbol in alphabet | variables):
        raise PostaError("Алфавитные символы и переменные должны быть односимвольными")
    axiom = parsed["A1"][0]
    _validate_word(axiom, alphabet, variables, allow_variables=False)
    for rule in rules:
        for token in rule.lhs + rule.rhs:
            if token.islower() and token not in variables:
                raise PostaError(f"Переменная '{token}' отсутствует в множестве X")
            if not token.islower() and token not in alphabet:
                raise PostaError(f"Символ '{token}' отсутствует во внешнем алфавите")
    return alphabet, variables, axiom, rules


def _validate_word(word: str, alphabet: set[str], variables: set[str], *, allow_variables: bool) -> None:
    for token in word:
        if token in alphabet:
            continue
        if allow_variables and token in variables:
            continue
        raise PostaError(f"Символ '{token}' отсутствует во внешнем алфавите")


def _match(pattern: str, word: str, variables: set[str]) -> dict[str, str] | None:
    """Полностью сопоставляет левую часть продукции со строкой."""
    bindings: dict[str, str] = {}

    def visit(pattern_pos: int, word_pos: int) -> dict[str, str] | None:
        if pattern_pos == len(pattern):
            return dict(bindings) if word_pos == len(word) else None
        token = pattern[pattern_pos]
        if token not in variables:
            if word_pos < len(word) and word[word_pos] == token:
                return visit(pattern_pos + 1, word_pos + 1)
            return None

        if token in bindings:
            value = bindings[token]
            if word.startswith(value, word_pos):
                return visit(pattern_pos + 1, word_pos + len(value))
            return None

        # Для данной работы переменные обозначают унарные слова из символов 1.
        for end in range(word_pos, len(word) + 1):
            value = word[word_pos:end]
            if any(symbol != "1" for symbol in value):
                break
            bindings[token] = value
            result = visit(pattern_pos + 1, end)
            if result is not None:
                return result
            bindings.pop(token, None)
        return None

    return visit(0, 0)


def _substitute(pattern: str, bindings: dict[str, str], variables: set[str]) -> str:
    return "".join(bindings[token] if token in variables else token for token in pattern)


def _format_trace(result: PostaResult) -> str:
    lines = [
        "Эмулятор канонической системы Поста, вариант 20",
        f"Исходная строка: {result.initial_word}",
        "",
    ]
    for entry in result.trace:
        lines.extend(
            [
                f"Шаг {entry.step}",
                f"Исходная строка: {entry.before}",
                f"Применено правило: {entry.rule.text}",
                f"Результат применения: {entry.after}",
                "",
            ]
        )
    lines.extend(
        [
            "Вычисление прошло успешно",
            f"Итоговая строка: {result.final_word}",
            f"Результат: {result.result}",
            f"Количество шагов: {result.steps}",
        ]
    )
    return "\n".join(lines) + "\n"


def run_system(
    config_path: str | Path,
    output_path: str | Path | None = None,
    max_steps: int = 10000,
) -> PostaResult:
    alphabet, variables, current, rules = parse_system(config_path)
    initial = current
    trace: list[TraceEntry] = []
    for step in range(1, max_steps + 1):
        applied = False
        for rule in rules:
            bindings = _match(rule.lhs, current, variables)
            if bindings is None:
                continue
            next_word = _substitute(rule.rhs, bindings, variables)
            _validate_word(next_word, alphabet, variables, allow_variables=False)
            trace.append(TraceEntry(step, current, rule, next_word))
            current = next_word
            applied = True
            break
        if not applied:
            if not re.fullmatch(r"=1*", current):
                raise PostaError(
                    f"Вычисление остановлено в некорректной конфигурации: {current}"
                )
            result = PostaResult(initial, current, current[1:], len(trace), True, tuple(trace))
            if output_path is not None:
                Path(output_path).write_text(_format_trace(result), encoding="utf-8")
            return result
    raise PostaError(f"Превышено ограничение в {max_steps} шагов")


def main() -> int:
    parser = argparse.ArgumentParser(description="Эмулятор канонической системы Поста")
    parser.add_argument("--input", required=True, help="файл с описанием FS_p")
    parser.add_argument("--output", required=True, help="файл протокола выполнения")
    args = parser.parse_args()
    try:
        result = run_system(args.input, args.output)
    except (OSError, PostaError) as error:
        print(f"Вычисление завершилось ошибкой: {error}")
        return 1
    print("Вычисление прошло успешно")
    print(f"Результат: {result.result}")
    print(f"Шагов: {result.steps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
