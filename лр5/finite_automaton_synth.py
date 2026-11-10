"""Synthesize a deterministic finite automaton from the lab regex notation."""
from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from pathlib import Path


END = object()


@dataclass(frozen=True)
class Node:
    kind: str
    value: str | None = None
    children: tuple["Node", ...] = ()


@dataclass
class Automaton:
    expression: str
    alphabet: list[str]
    states: list[str]
    transitions: dict[tuple[str, str], str]
    accepting: set[str]
    state_places: dict[str, set[int]]
    place_symbols: dict[int, str]

    def accepts(self, word: str) -> bool:
        state = "q0"
        for symbol in word:
            state = self.transitions.get((state, symbol))
            if state is None:
                return False
        return state in self.accepting

    def transition_matrix(self) -> list[list[str]]:
        return [[self.transitions.get((state, symbol), "—") for symbol in self.alphabet]
                for state in self.states]

    def automaton_matrix(self) -> list[list[str]]:
        result = []
        for state in self.states:
            row = []
            for symbol in self.alphabet:
                target = self.transitions.get((state, symbol))
                if target is None:
                    row.append("—")
                else:
                    output = "1" if target in self.accepting else "0"
                    row.append(f"{target}/{output}")
            result.append(row)
        return result

    def matrix_text(self) -> str:
        widths = [max(5, *(len(row[i]) for row in self.automaton_matrix()))
                  for i in range(len(self.alphabet))]
        state_width = max(7, *(len(state) for state in self.states))
        header = f"{'Q\\X':<{state_width}} " + " ".join(
            f"{symbol:>{widths[i]}}" for i, symbol in enumerate(self.alphabet))
        lines = [f"Регулярное выражение: {self.expression}",
                 f"Начальное состояние: q0; допускающие: {', '.join(sorted(self.accepting, key=self.states.index))}",
                 "Матрица автомата (ячейка: следующее состояние/выход):", header]
        for state, row in zip(self.states, self.automaton_matrix()):
            lines.append(f"{state:<{state_width}} " + " ".join(
                f"{value:>{widths[i]}}" for i, value in enumerate(row)))
        lines.append("\nМножества активных мест:")
        for state in self.states:
            places = self.state_places[state]
            labels = [f"{i}:{self.place_symbols[i]}" for i in sorted(places) if i and i in self.place_symbols]
            if labels:
                lines.append(f"{state}: {{{', '.join(labels)}}}")
            else:
                lines.append(f"{state}: {{0}}" if state == "q0" else f"{state}: {{}}")
        return "\n".join(lines) + "\n"


class Parser:
    def __init__(self, source: str):
        self.source = "".join(source.split())
        self.i = 0

    def parse(self) -> Node:
        node = self.alternation()
        if self.i != len(self.source):
            raise ValueError(f"Неожиданный символ {self.source[self.i]!r} в позиции {self.i + 1}")
        return node

    def alternation(self) -> Node:
        parts = [self.concatenation()]
        while self.peek() == "|":
            self.i += 1
            parts.append(self.concatenation())
        return parts[0] if len(parts) == 1 else Node("alt", children=tuple(parts))

    def concatenation(self) -> Node:
        parts = []
        while self.i < len(self.source) and self.peek() not in ")|⟩":
            parts.append(self.repetition())
        if not parts:
            raise ValueError("Пустой фрагмент регулярного выражения не поддерживается")
        return parts[0] if len(parts) == 1 else Node("cat", children=tuple(parts))

    def repetition(self) -> Node:
        if self.peek() == "⟨":
            self.i += 1
            child = self.alternation()
            if self.peek() != "⟩":
                raise ValueError("Для итерации отсутствует закрывающая скобка ⟩")
            self.i += 1
            return Node("star", children=(child,))
        if self.peek() == "(":
            self.i += 1
            child = self.alternation()
            if self.peek() != ")":
                raise ValueError("Для группы отсутствует закрывающая скобка )")
            self.i += 1
            return child
        char = self.peek()
        if char is None or char in "|)⟩":
            raise ValueError(f"Ожидался символ или группа в позиции {self.i + 1}")
        if char in "()⟨":
            raise ValueError(f"Неожиданная скобка {char!r} в позиции {self.i + 1}")
        self.i += 1
        return Node("lit", char)

    def peek(self) -> str | None:
        return self.source[self.i] if self.i < len(self.source) else None


def synthesize(expression: str) -> Automaton:
    """Use marked symbol places, follow relations, determinization, and state merging."""
    tree = Parser(expression).parse()
    next_place = 1
    place_symbols: dict[int, str] = {}

    def number(node: Node) -> Node:
        nonlocal next_place
        if node.kind == "lit":
            place = next_place
            next_place += 1
            place_symbols[place] = node.value or ""
            return Node("pos", str(place))
        return Node(node.kind, node.value, tuple(number(child) for child in node.children))

    numbered = number(tree)
    end_place = next_place
    augmented = Node("cat", children=(numbered, Node("pos", str(end_place))))
    place_symbols[end_place] = "#"
    follow: dict[int, set[int]] = {i: set() for i in place_symbols}

    def properties(node: Node) -> tuple[bool, set[int], set[int]]:
        if node.kind == "pos":
            pos = int(node.value or "0")
            return False, {pos}, {pos}
        if node.kind == "alt":
            props = [properties(child) for child in node.children]
            return (any(p[0] for p in props),
                    set().union(*(p[1] for p in props)),
                    set().union(*(p[2] for p in props)))
        if node.kind == "cat":
            props = [properties(child) for child in node.children]
            nullable = True
            first: set[int] = set()
            for child_nullable, child_first, _ in props:
                first.update(child_first)
                if not child_nullable:
                    nullable = False
                    break
            last: set[int] = set()
            for child_nullable, _, child_last in reversed(props):
                last.update(child_last)
                if not child_nullable:
                    break
            for i, (left_nullable, _, left_last) in enumerate(props[:-1]):
                suffix_first: set[int] = set()
                for right_nullable, right_first, _ in props[i + 1:]:
                    suffix_first.update(right_first)
                    if not right_nullable:
                        break
                for pos in left_last:
                    follow[pos].update(suffix_first)
            return nullable, first, last
        if node.kind == "star":
            nullable, first, last = properties(node.children[0])
            for pos in last:
                follow[pos].update(first)
            return True, first, last
        raise ValueError(f"Неизвестный узел выражения: {node.kind}")

    _, firstpos, _ = properties(augmented)
    alphabet = sorted(set(place_symbols.values()) - {"#"})

    # DFA states are sets of active places; state 0 uses firstpos as its outgoing places.
    start = frozenset(firstpos)
    dfa_states = [start]
    seen = {start}
    transitions: dict[tuple[frozenset[int], str], frozenset[int]] = {}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for symbol in alphabet:
            matched = {pos for pos in state if place_symbols[pos] == symbol}
            target = frozenset().union(*(follow[pos] for pos in matched)) if matched else frozenset()
            if not target:
                continue
            transitions[(state, symbol)] = target
            if target not in seen:
                seen.add(target)
                dfa_states.append(target)
                queue.append(target)

    finals = {state for state in dfa_states if end_place in state}
    # Partition refinement merges states with identical future behavior.
    blocks = [block for block in (finals, set(dfa_states) - finals) if block]
    changed = True
    while changed:
        changed = False
        block_of = {state: i for i, block in enumerate(blocks) for state in block}
        refined = []
        for block in blocks:
            groups: dict[tuple[int, ...], set[frozenset[int]]] = {}
            for state in block:
                signature = tuple(block_of.get(transitions.get((state, symbol)), -1) for symbol in alphabet)
                groups.setdefault(signature, set()).add(state)
            refined.extend(groups.values())
            changed |= len(groups) > 1
        blocks = refined

    block_of = {state: i for i, block in enumerate(blocks) for state in block}
    start_block = block_of[start]
    incoming_places = {i: set() for i in range(len(blocks))}
    for source_state in dfa_states:
        for symbol in alphabet:
            target_state = transitions.get((source_state, symbol))
            if target_state is None:
                continue
            target_block = block_of[target_state]
            incoming_places[target_block].update(
                pos for pos in source_state if place_symbols[pos] == symbol
            )
    # Number the minimized states by breadth-first traversal from the initial state.
    order = [start_block]
    block_name = {start_block: "q0"}
    for current in order:
        representative = next(iter(blocks[current]))
        for symbol in alphabet:
            target = transitions.get((representative, symbol))
            if target is None:
                continue
            target_block = block_of[target]
            if target_block not in block_name:
                block_name[target_block] = f"q{len(block_name)}"
                order.append(target_block)

    states = [block_name[i] for i in order]
    minimized_transitions = {}
    accepting = set()
    state_places: dict[str, set[int]] = {"q0": {0}}
    for b in order:
        name = block_name[b]
        block = blocks[b]
        if block & finals:
            accepting.add(name)
        state_places[name] = {0} if name == "q0" else incoming_places[b]
        representative = next(iter(block))
        for symbol in alphabet:
            target = transitions.get((representative, symbol))
            if target is not None:
                minimized_transitions[(name, symbol)] = block_name[block_of[target]]

    # Place 0 denotes the initial place before the first input symbol.
    place_symbols[0] = "—"
    return Automaton(expression, alphabet, states, minimized_transitions, accepting,
                     state_places, place_symbols)


def main() -> None:
    parser = argparse.ArgumentParser(description="Синтез КНА по регулярному выражению")
    parser.add_argument("input", nargs="?", default="data/variant20.regex", help="текстовый файл с выражением")
    parser.add_argument("-o", "--output", default="output/variant20_automaton.txt", help="файл матрицы автомата")
    args = parser.parse_args()
    source_path, output_path = Path(args.input), Path(args.output)
    expression = source_path.read_text(encoding="utf-8-sig").strip()
    automaton = synthesize(expression)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(automaton.matrix_text(), encoding="utf-8")
    print(f"Автомат синтезирован: {len(automaton.states)} состояний, алфавит {{{', '.join(automaton.alphabet)}}}.")
    print(f"Матрица записана в {output_path}")


if __name__ == "__main__":
    main()
