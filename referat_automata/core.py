"""Синтез по местам ЛР5 и минимизация Мили по лекционному разбиению."""
from collections import deque
from dataclasses import dataclass, field
import string


class InputError(ValueError):
    """Ожидаемая ошибка входных данных или установленного лимита."""


@dataclass
class Machine:
    alphabet: list
    states: list
    start: str
    transitions: dict
    finals: set = field(default_factory=set)
    recognizer: bool = False
    details: dict = field(default_factory=dict)

    def to_dict(self):
        result = {'alphabet': self.alphabet, 'states': self.states,
                  'start': self.start, 'transitions': self.transitions,
                  'recognizer': self.recognizer}
        if self.recognizer:
            result['finals'] = sorted(self.finals)
        return result


class Places:
    """Места — зазоры между токенами; p→r означает r подчинено p."""
    def __init__(self, source):
        if not isinstance(source, str):
            raise InputError('Регулярное выражение должно быть строкой.')
        self.text = ''.join(source.split()).replace('⟨', '<').replace('⟩', '>')
        if not self.text:
            raise InputError('Введите регулярное выражение.')
        if len(self.text) > 300:
            raise InputError('Выражение длиннее 300 символов.')
        self.i = 0
        self.edges = {i: set() for i in range(len(self.text) + 1)}
        self.letters = []
        self.depth = 0
        branches = self.expression()
        self.ends = {finish for _, finish in branches}
        if self.i != len(self.text):
            self.fail('Лишняя закрывающая скобка')
        self.main = {start: 0 for start, _ in branches}
        for index, (_, _, end) in enumerate(self.letters, 1):
            self.main[end] = index
        self.closure = {}
        for place in self.edges:
            seen, pending = {place}, [place]
            while pending:
                for nxt in self.edges[pending.pop()] - seen:
                    seen.add(nxt)
                    pending.append(nxt)
            self.closure[place] = seen

    def fail(self, message):
        raise InputError(f'{message}. Позиция {self.i + 1}.')

    def expression(self):
        start, end = self.sequence()
        branches = [(start, end)]
        while self.i < len(self.text) and self.text[self.i] == '|':
            self.i += 1
            branches.append(self.sequence())
        return branches

    def sequence(self):
        start = self.i
        if self.i == len(self.text) or self.text[self.i] in '|)>':
            self.fail('Пустая ветвь; для пустого слова используйте ε')
        while self.i < len(self.text) and self.text[self.i] not in '|)>':
            c, begin = self.text[self.i], self.i
            if c in '(<':
                self.depth += 1
                if self.depth > 40:
                    self.fail('Глубина вложенности больше 40')
                self.i += 1
                branches = self.expression()
                close = ')' if c == '(' else '>'
                if self.i == len(self.text) or self.text[self.i] != close:
                    self.fail(f'Ожидалась скобка {close}')
                self.i += 1
                self.depth -= 1
                for body_start, body_end in branches:
                    self.edges[begin].add(body_start)
                    self.edges[body_end].add(self.i)
                if c == '<':
                    self.edges[begin].add(self.i)
                    self.edges[self.i].update(s for s, _ in branches)
            elif c in string.ascii_letters + string.digits:
                self.i += 1
                self.letters.append((c, begin, self.i))
            elif c == 'ε':
                self.i += 1
                self.edges[begin].add(self.i)
            else:
                self.fail(f'Недопустимый символ «{c}»')
        return start, self.i


def synthesize(text, max_states=256):
    if type(max_states) is not int or not 1 <= max_states <= 512:
        raise InputError('Лимит состояний должен быть целым числом от 1 до 512.')
    p = Places(text)
    alphabet = sorted({letter for letter, _, _ in p.letters})
    by_index = {}
    for place, index in p.main.items():
        by_index.setdefault(index, set()).update(p.closure[place])
    initial = frozenset({0})
    subsets, names, transitions, finals = [initial], {initial: 'q0'}, {}, set()
    pending = deque([initial])
    while pending:
        subset = pending.popleft()
        name = names[subset]
        active = set().union(*(by_index[i] for i in subset))
        if p.ends & active:
            finals.add(name)
        transitions[name] = {}
        for symbol in alphabet:
            target = frozenset(p.main[end] for c, begin, end in p.letters
                               if c == symbol and begin in active)
            if target not in names:
                if len(names) >= max_states:
                    raise InputError(f'Превышен лимит {max_states} состояний.')
                names[target] = f'q{len(names)}'
                subsets.append(target)
                pending.append(target)
            reached = set().union(*(by_index[i] for i in target))
            transitions[name][symbol] = [names[target],
                                         '1' if p.ends & reached else '0']
    places = []
    for gap in p.edges:
        indices = sorted({index for origin, index in p.main.items()
                          if gap in p.closure[origin]})
        places.append({'place': gap, 'before': p.text[gap-1] if gap else '—',
                       'after': p.text[gap] if gap < len(p.text) else '—',
                       'main': p.main.get(gap), 'indices': indices,
                       'subordinates': sorted(p.closure[gap])})
    details = {'expression': p.text, 'places': places, 'end_places': sorted(p.ends),
               'subsets': {names[s]: sorted(s) for s in subsets},
               'edges': {str(k): sorted(v - {k}) for k, v in p.edges.items()}}
    return Machine(alphabet, list(transitions), 'q0', transitions, finals, True, details)


def from_dict(data):
    if not isinstance(data, dict):
        raise InputError('JSON должен содержать объект автомата.')
    def names(key, allow_empty=False):
        value = data.get(key)
        if not isinstance(value, list) or (not value and not allow_empty):
            raise InputError(f'Поле {key}: ожидается список.')
        if any(not isinstance(x, str) or not x or len(x) > 40 for x in value):
            raise InputError(f'Поле {key}: нужны непустые строки длиной до 40.')
        if len(set(value)) != len(value):
            raise InputError(f'Поле {key}: повторяющиеся элементы.')
        return value
    states, alphabet = names('states'), names('alphabet', True)
    if len(states) > 512 or len(alphabet) > 62:
        raise InputError('Допускается до 512 состояний и до 62 входных символов.')
    if any(len(c) != 1 or c.isspace() for c in alphabet):
        raise InputError('Входной символ должен быть одним непробельным знаком.')
    start = data.get('start')
    if not isinstance(start, str) or start not in states:
        raise InputError('Начальное состояние не принадлежит states.')
    recog = data.get('recognizer', False)
    if type(recog) is not bool:
        raise InputError('recognizer должен быть true или false.')
    finals = data.get('finals', [])
    if not isinstance(finals, list) or any(not isinstance(q, str) or q not in states for q in finals):
        raise InputError('finals должен содержать только объявленные состояния.')
    if not recog and finals:
        raise InputError('Для finals требуется recognizer=true.')
    raw = data.get('transitions')
    if not isinstance(raw, dict) or set(raw) != set(states):
        raise InputError('В transitions нужны строки всех и только объявленных состояний.')
    transitions = {}
    for q in states:
        row = raw[q]
        if not isinstance(row, dict) or set(row) != set(alphabet):
            raise InputError(f'{q}: задайте ровно один переход на каждый символ алфавита.')
        transitions[q] = {}
        for x, cell in row.items():
            if not isinstance(cell, list) or len(cell) != 2:
                raise InputError(f'{q}, {x}: нужна пара [состояние, выход].')
            target, output = cell
            if not isinstance(target, str) or target not in states:
                raise InputError(f'{q}, {x}: неизвестное состояние назначения.')
            if type(output) not in (str, int) or not str(output) or len(str(output)) > 40:
                raise InputError(f'{q}, {x}: выход — строка или целое число длиной до 40.')
            if recog and str(output) != ('1' if target in finals else '0'):
                raise InputError(f'{q}, {x}: выход распознавателя должен совпадать с конечностью цели.')
            transitions[q][x] = [target, str(output)]
    return Machine(alphabet, states, start, transitions, set(finals), recog)


def lecture_machine():
    return from_dict({'alphabet': ['x', 'y'], 'states': ['q1','q2','q3','q4','q5'],
        'start': 'q1', 'transitions': {
        'q1': {'x': ['q2',1], 'y': ['q3',0]},
        'q2': {'x': ['q2',1], 'y': ['q3',0]},
        'q3': {'x': ['q4',2], 'y': ['q3',0]},
        'q4': {'x': ['q4',2], 'y': ['q5',3]},
        'q5': {'x': ['q4',2], 'y': ['q5',3]}}})


def reachable(machine):
    seen, todo = {machine.start}, [machine.start]
    while todo:
        for nxt, _ in machine.transitions[todo.pop()].values():
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return [q for q in machine.states if q in seen]


def minimize(machine):
    states = reachable(machine)
    groups = {}
    for q in states:
        key = tuple(machine.transitions[q][x][1] for x in machine.alphabet)
        if machine.recognizer:
            key += (q in machine.finals,)
        groups.setdefault(key, []).append(q)
    partition = list(groups.values())
    history = [partition]
    while True:
        owner = {q: i for i, block in enumerate(partition) for q in block}
        refined = []
        for block in partition:
            pieces = {}
            for q in block:
                signature = tuple(owner[machine.transitions[q][x][0]] for x in machine.alphabet)
                pieces.setdefault(signature, []).append(q)
            refined.extend(pieces.values())
        history.append(refined)
        if refined == partition:
            break
        partition = refined
    names = [chr(65+i) if i < 26 else f'C{i}' for i in range(len(partition))]
    mapping = {q: names[i] for i, block in enumerate(partition) for q in block}
    transitions = {}
    for name, block in zip(names, partition):
        transitions[name] = {x: [mapping[machine.transitions[block[0]][x][0]],
                                  machine.transitions[block[0]][x][1]] for x in machine.alphabet}
    finals = {mapping[q] for q in machine.finals if q in mapping}
    result = Machine(machine.alphabet[:], names, mapping[machine.start], transitions,
                     finals, machine.recognizer)
    return result, history, mapping


def run(machine, word):
    if not isinstance(word, str) or len(word) > 10000:
        raise InputError('Слово должно быть строкой длиной до 10000 символов.')
    q, trace, outputs = machine.start, [], []
    for i, x in enumerate(word):
        if x not in machine.alphabet:
            return {'accepted': False if machine.recognizer else None,
                    'error': f'Символ «{x}» не входит в алфавит (позиция {i+1}).',
                    'trace': trace, 'outputs': outputs, 'state': q}
        target, output = machine.transitions[q][x]
        trace.append([i+1, q, x, target, output])
        outputs.append(output)
        q = target
    return {'accepted': q in machine.finals if machine.recognizer else None,
            'error': None, 'trace': trace, 'outputs': outputs, 'state': q}


def compare(a, b):
    if set(a.alphabet) != set(b.alphabet) or a.recognizer != b.recognizer:
        return {'equivalent': False, 'witness': '', 'pairs': 0,
                'reason': 'Разные алфавиты или режимы.'}
    queue = deque([(a.start, b.start, '')])
    seen = {(a.start, b.start)}
    while queue:
        p, q, prefix = queue.popleft()
        if a.recognizer and ((p in a.finals) != (q in b.finals)):
            return {'equivalent': False, 'witness': prefix, 'pairs': len(seen),
                    'reason': 'Различается допустимость слова.'}
        for x in a.alphabet:
            ap, ao = a.transitions[p][x]
            bp, bo = b.transitions[q][x]
            if ao != bo:
                return {'equivalent': False, 'witness': prefix+x, 'pairs': len(seen),
                        'reason': 'Различаются выходные сигналы.'}
            if (ap, bp) not in seen:
                seen.add((ap, bp))
                queue.append((ap, bp, prefix+x))
    return {'equivalent': True, 'witness': None, 'pairs': len(seen),
            'reason': 'Все достижимые пары проверены.'}
