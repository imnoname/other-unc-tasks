"""UTF-8 ввод и воспроизводимый экспорт таблиц, графов и протокола."""
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape
from core import InputError, compare


def load_input(path):
    try:
        path = Path(path)
        if path.stat().st_size > 32_000_000:
            raise InputError('Входной файл больше 32 МБ.')
        text = path.read_text(encoding='utf-8-sig')
        return ('Мили JSON' if path.suffix.lower() == '.json' else 'РВ'), text
    except (OSError, UnicodeError) as error:
        raise InputError(f'Не удалось прочитать файл: {error}') from error


def table(headers, rows):
    cells = [[str(x) for x in headers]] + [[str(x) for x in row] for row in rows]
    widths = [max(len(row[i]) for row in cells) for i in range(len(headers))]
    return '\n'.join(' | '.join(x.ljust(widths[i]) for i, x in enumerate(row)) for row in cells)


def transition_text(m):
    rows = []
    for q in m.states:
        tag = ('→' if q == m.start else '') + ('*' if q in m.finals else '') + q
        rows.append([tag] + [f'{m.transitions[q][x][0]}/{m.transitions[q][x][1]}' for x in m.alphabet])
    return table(['Q / X'] + m.alphabet, rows)


def matrix_text(m):
    rows = []
    for q in m.states:
        rows.append([q] + [', '.join(f'{x}/{out}' for x, (target,out) in m.transitions[q].items()
                                    if target == t) or '—' for t in m.states])
    return table(['Q / Q'] + m.states, rows)


def graph_layout(m):
    count = len(m.states)
    radius = max(100, min(1100, count * 25)) if count > 1 else 0
    center = radius + 90
    positions = {q: (center + radius * math.cos(2*math.pi*i/count-math.pi/2),
                     center + radius * math.sin(2*math.pi*i/count-math.pi/2))
                 for i,q in enumerate(m.states)}
    return positions, int(2*center+30)


def graph_svg(m):
    positions, size = graph_layout(m)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
      '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6" fill="#334155"/></marker></defs>',
      '<rect width="100%" height="100%" fill="white"/>']
    for q in m.states:
        grouped = {}
        for x,(t,out) in m.transitions[q].items():
            grouped.setdefault(t,[]).append(f'{x}/{out}')
        x1,y1 = positions[q]
        for t, labels in grouped.items():
            x2,y2 = positions[t]
            label = escape(', '.join(labels))
            if q == t:
                parts.append(f'<path d="M{x1-14},{y1-22} C{x1-58},{y1-86} {x1+58},{y1-86} {x1+14},{y1-22}" fill="none" stroke="#334155" marker-end="url(#arrow)"/>')
                lx,ly=x1,y1-68
            else:
                dx,dy=x2-x1,y2-y1; norm=math.hypot(dx,dy)
                sx,sy=x1+dx*28/norm,y1+dy*28/norm
                ex,ey=x2-dx*30/norm,y2-dy*30/norm
                cx,cy=(x1+x2)/2-dy*.16,(y1+y2)/2+dx*.16
                parts.append(f'<path d="M{sx},{sy} Q{cx},{cy} {ex},{ey}" fill="none" stroke="#334155" marker-end="url(#arrow)"/>')
                lx,ly=(sx+ex+2*cx)/4,(sy+ey+2*cy)/4-5
            parts.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="Arial" font-size="13" fill="#1e40af">{label}</text>')
    for q,(x,y) in positions.items():
        parts.append(f'<circle cx="{x}" cy="{y}" r="26" stroke="#334155" fill="#e0f2fe"/>')
        if q in m.finals:
            parts.append(f'<circle cx="{x}" cy="{y}" r="22" stroke="#334155" fill="none"/>')
        if q == m.start:
            parts.append(f'<path d="M{x-65},{y} L{x-28},{y}" stroke="#334155" marker-end="url(#arrow)"/>')
        parts.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" font-family="Arial" font-size="15">{escape(q)}</text>')
    return '\n'.join(parts+['</svg>'])


def protocol(m, small, partitions, mapping):
    lines = ['СИНТЕЗ И МИНИМИЗАЦИЯ КОНЕЧНОГО АВТОМАТА',
      'Исходный автомат (цель/выход)', transition_text(m),
      '\nМатрица исходного автомата', matrix_text(m), '\nРазбиения']
    for i, blocks in enumerate(partitions):
        lines.append(f'P{i}: ' + ' | '.join('{'+', '.join(b)+'}' for b in blocks))
    lines += ['\nСоответствие состояний', json.dumps(mapping,ensure_ascii=False),
              '\nМинимальный автомат', transition_text(small),
              '\nМатрица минимального автомата', matrix_text(small),
              '\nТочная проверка эквивалентности', json.dumps(compare(m,small),ensure_ascii=False)]
    if m.details:
        lines += ['\nМеста и индексы', json.dumps(m.details,ensure_ascii=False,indent=2)]
    return '\n'.join(lines)


def export_bundle(folder, m, small, partitions, mapping):
    try:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        payload = {'original.json': json.dumps(m.to_dict(),ensure_ascii=False,indent=2),
                   'minimal.json': json.dumps(small.to_dict(),ensure_ascii=False,indent=2),
                   'protocol.txt': protocol(m,small,partitions,mapping),
                   'original.svg': graph_svg(m), 'minimal.svg': graph_svg(small)}
        for name, contents in payload.items():
            (folder/name).write_text(contents,encoding='utf-8')
        return list(payload)
    except OSError as error:
        raise InputError(f'Не удалось сохранить комплект: {error}') from error
