from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "lab_title.docx"
OUTPUT = ROOT / "Отчет_ЛР4_вариант20.docx"
DIAGRAM = ROOT / "Диаграмма_КНА_вариант20.png"

STATES = ["q0", "q1", "q2", "q3"]
ALPHABET = ["a", "b", "c", "d", "e"]
TRANSITIONS = {
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
OUTPUTS = {(state, symbol): ("1" if symbol == "e" else "0") for state, symbol in TRANSITIONS}


def font(run, size=14, bold=None, name="Times New Roman"):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def add_page_number(paragraph):
    run = paragraph.add_run()
    for kind, value in (("begin", None), ("instrText", "PAGE"), ("separate", None), ("t", "1"), ("end", None)):
        node = OxmlElement(f"w:{kind}" if kind in ("instrText", "t") else "w:fldChar")
        if kind in ("begin", "separate", "end"):
            node.set(qn("w:fldCharType"), kind)
        elif kind == "instrText":
            node.set(qn("xml:space"), "preserve")
            node.text = value
        else:
            node.text = value
        run._r.append(node)


def set_cell(cell, value, size=10, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(str(value))
    font(r, size, bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def borders(table):
    root = table._tbl.tblPr
    edge_set = root.first_child_found_in("w:tblBorders")
    if edge_set is None:
        edge_set = OxmlElement("w:tblBorders")
        root.append(edge_set)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:color"), "777777")
        edge_set.append(node)


def table(doc, caption, headers, rows, size=10):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    font(p.add_run(caption), 12, True)
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = True
    borders(t)
    for i, item in enumerate(headers):
        set_cell(t.rows[0].cells[i], item, size, True)
    for row in rows:
        cells = t.add_row().cells
        for i, item in enumerate(row):
            set_cell(cells[i], item, size)
    doc.add_paragraph()
    return t


def body(doc, text):
    p = doc.add_paragraph(style="Normal")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25)
    r = p.add_run(text)
    font(r)
    return p


def heading(doc, text, page_break=True):
    p = doc.add_paragraph(style="Heading 1")
    p.paragraph_format.page_break_before = page_break
    p.paragraph_format.first_line_indent = Cm(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run(text), 14, True)
    return p


def draw_graph():
    im = Image.new("RGB", (1500, 720), "white")
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/times.ttf", 28)
        fs = ImageFont.truetype("C:/Windows/Fonts/times.ttf", 24)
    except OSError:
        f = fs = ImageFont.load_default()
    coords = {"q0": (160, 350), "q1": (500, 350), "q2": (870, 350), "q3": (1240, 350)}
    radius = 52
    d.line((42, 350, 98, 350), fill="black", width=3)
    d.polygon([(98, 350), (80, 340), (80, 360)], fill="black")

    def arrow(points, label, label_pos):
        d.line(points, fill="black", width=3)
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        tip = (x2, y2)
        left = (x2 - 16 * math.cos(angle) + 8 * math.sin(angle), y2 - 16 * math.sin(angle) - 8 * math.cos(angle))
        right = (x2 - 16 * math.cos(angle) - 8 * math.sin(angle), y2 - 16 * math.sin(angle) + 8 * math.cos(angle))
        d.polygon([tip, left, right], fill="black")
        d.text(label_pos, label, fill="black", font=fs)

    for state, (x, y) in coords.items():
        d.ellipse((x-radius, y-radius, x+radius, y+radius), outline="black", width=3)
        if state != "q0":
            d.ellipse((x-radius+7, y-radius+7, x+radius-7, y+radius-7), outline="black", width=2)
        box = d.textbbox((0, 0), state, font=f)
        d.text((x-(box[2]-box[0])/2, y-(box[3]-box[1])/2-4), state, fill="black", font=f)
    arrow([(212, 350), (445, 350)], "a/0", (310, 305))
    def loop(x, label):
        d.arc((x-38, 190, x+38, 285), start=180, end=360, fill="black", width=3)
        d.line((x+38, 237, x+30, 295), fill="black", width=3)
        d.polygon([(x+30, 295), (x+22, 279), (x+39, 281)], fill="black")
        d.text((x+45, 215), label, fill="black", font=fs)
    loop(500, "b/0")
    arrow([(552, 350), (815, 350)], "c/0, d/0", (650, 305))
    loop(870, "c/0, d/0")
    arrow([(922, 350), (1185, 350)], "e/1", (1030, 305))
    loop(1240, "e/1")
    arrow([(552, 382), (570, 470), (660, 510), (760, 470), (815, 382)], "e/1", (650, 480))
    im.save(DIAGRAM)


def build():
    draw_graph()
    doc = Document(str(TEMPLATE))
    sec = doc.sections[0]
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)
    sec.left_margin, sec.right_margin = Cm(3), Cm(1.5)
    sec.different_first_page_header_footer = True
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(14)
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for n in ("Heading 1", "Heading 2"):
        style = doc.styles[n]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(14)
        style.font.bold = True
        style.paragraph_format.keep_with_next = True
    footer = sec.footer.paragraphs[0]
    clear_paragraph(footer)
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(footer)

    # Official GUAP title page form: preserve field layout and labels.
    for i, text in ((1, "КАФЕДРА № 43"), (7, "Санкт-Петербург 2026")):
        doc.paragraphs[i].text = text
        doc.paragraphs[i].alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.paragraphs[i].paragraph_format.first_line_indent = Pt(0)
        doc.paragraphs[i].paragraph_format.line_spacing = 1.0
        for run in doc.paragraphs[i].runs:
            font(run, 14)
    for i in (2, 3):
        doc.paragraphs[i].paragraph_format.first_line_indent = Pt(0)
        doc.paragraphs[i].paragraph_format.line_spacing = 1.0
    teacher = doc.tables[0]
    set_cell(teacher.cell(0, 4), "Рогачев С. А.", 10)
    set_cell(teacher.cell(1, 4), "инициалы, фамилия", 9)
    title = doc.tables[1]
    set_cell(title.cell(0, 0), "ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 4", 13, True)
    set_cell(title.cell(1, 0), "Исследование алгоритмов задания конечных автоматов\nВариант 20", 11)
    set_cell(title.cell(2, 0), "по курсу: Теория вычислительных процессов", 10)
    for row in list(title.rows)[3:]:
        title._tbl.remove(row._tr)
    student = doc.tables[2]
    set_cell(student.cell(0, 1), "4332", 12)
    set_cell(student.cell(0, 5), "Могилатов С. И.", 12)
    set_cell(student.cell(1, 3), "подпись, дата", 9)
    set_cell(student.cell(1, 5), "инициалы, фамилия", 9)
    doc.add_page_break()

    heading(doc, "СОДЕРЖАНИЕ", False)
    toc = [
        ("Цель работы", "3"), ("Постановка задачи", "4"),
        ("Построение конечного автомата", "5"), ("Задание автомата тремя способами", "6"),
        ("Проверка допустимости входных слов", "8"), ("Вывод", "9"),
        ("Контрольные вопросы", "10"), ("Список литературы", "12"),
    ]
    for label, page in toc:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(1.25)
        font(p.add_run(f"{label} ........................................ {page}"))

    heading(doc, "ЦЕЛЬ РАБОТЫ")
    body(doc, "Изучить способы задания конечных автоматов и приобрести навыки построения автоматной модели по регулярному выражению. Для регулярного выражения своего варианта требуется построить конечный автомат Мили, представить его таблицами переходов и выходов, ориентированным графом и матрицей переходов-выходов, а затем проверить допустимость входных слов.")

    heading(doc, "ПОСТАНОВКА ЗАДАЧИ")
    body(doc, "Номер варианта — 20. Регулярное выражение: a⟨b⟩⟨(c|d)⟩⟨e⟩, где ⟨...⟩ означает повторение ноль или более раз, а | задаёт альтернативу.")
    body(doc, "Описание языка: слово обязательно начинается с a; далее может идти любое число символов b; затем любое число символов c или d; в конце может идти любое число символов e. Любая из трёх повторяемых частей может быть пустой. Поэтому слово a также принадлежит языку.")
    body(doc, "Примеры допустимых цепочек: a, ab, ac, ad, abbb, acd, abe, abce, acdeee. Примеры недопустимых цепочек: ba (нет начального a), acb (символ b встретился после начала блока c/d), aeb (после перехода к блоку e символ b недопустим).")

    heading(doc, "ПОСТРОЕНИЕ КОНЕЧНОГО АВТОМАТА")
    body(doc, "Построен детерминированный конечный автомат Мили S = ⟨X, Q, U, δ, λ⟩. Состояния отражают последовательные фазы регулярного выражения.")
    table(doc, "Таблица 1 — Множества автомата", ["Обозначение", "Содержание"], [
        ("Входной алфавит X", "{a, b, c, d, e}"),
        ("Множество состояний Q", "{q0, q1, q2, q3}"),
        ("Выходной алфавит U", "{0, 1}"),
        ("Начальное состояние", "q0"),
        ("Допускающие конечные состояния", "{q1, q2, q3}"),
    ], 11)
    body(doc, "Смысл состояний: q0 — начальное состояние, символ a ещё не прочитан; q1 — прочитан обязательный a, продолжается блок b*; q2 — начался блок (c|d)*; q3 — начался завершающий блок e*. Конечные состояния q1, q2 и q3 допускают окончание слова после любой из необязательных частей регулярного выражения.")
    body(doc, "Функция переходов δ определена следующими парами входного символа и состояния:")
    body(doc, "δ(a,q0)=q1; δ(b,q1)=q1; δ(c,q1)=q2; δ(d,q1)=q2; δ(c,q2)=q2; δ(d,q2)=q2; δ(e,q1)=q3; δ(e,q2)=q3; δ(e,q3)=q3. Для всех остальных пар δ не определена; такая конфигурация означает отклонение слова.")
    body(doc, "Функция выходов λ: на переходах по символам a, b, c, d выдаётся 0; на переходах по e выдаётся 1. Выход 1 отмечает чтение символа заключительной части e*. Допустимость всего слова определяется конечным состоянием после чтения всех символов: q1, q2 или q3 — слово допустимо. Это необходимо, поскольку завершающий цикл e* может содержать ноль символов.")

    heading(doc, "ЗАДАНИЕ АВТОМАТА ТРЕМЯ СПОСОБАМИ")
    body(doc, "Первый способ задания — таблица переходов δ. Прочерк означает, что переход не определён.")
    rows = [[q] + [TRANSITIONS.get((q, x), "—") for x in ALPHABET] for q in STATES]
    table(doc, "Таблица 2 — Таблица переходов δ", ["Состояние\\Вход", *ALPHABET], rows, 10)
    rows = [[q] + [OUTPUTS.get((q, x), "—") for x in ALPHABET] for q in STATES]
    table(doc, "Таблица 3 — Таблица выходов λ", ["Состояние\\Вход", *ALPHABET], rows, 10)
    body(doc, "Второй способ — ориентированный граф. Подпись каждой дуги имеет форму вход/выход; двойной круг обозначает допускающее конечное состояние.")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.add_run().add_picture(str(DIAGRAM), width=Cm(16))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    font(p.add_run("Рисунок 1 — Ориентированный граф автомата Мили варианта 20"), 12)
    p = body(doc, "Третий способ — матрица переходов-выходов. В ячейке указаны входные символы и выходы, переводящие автомат из состояния строки в состояние столбца.")
    p.paragraph_format.page_break_before = True
    matrix = [
        ("q0", "—", "a/0", "—", "—"),
        ("q1", "—", "b/0", "c/0, d/0", "e/1"),
        ("q2", "—", "—", "c/0, d/0", "e/1"),
        ("q3", "—", "—", "—", "e/1"),
    ]
    table(doc, "Таблица 4 — Матрица переходов-выходов", ["qi\\qj", *STATES], matrix, 10)

    heading(doc, "ПРОВЕРКА ДОПУСТИМОСТИ ВХОДНЫХ СЛОВ")
    body(doc, "Проверки выполнены последовательно для каждой пары (состояние, символ). Траектория показывает состояния от q0 до последнего достигнутого; «нет перехода» означает, что следующее входное сочетание отсутствует в автомате. В столбце выхода для такого шага указано «—».")
    checks = [
        ("a", "q0 → q1", "0", "Допустимо"),
        ("abbb", "q0 → q1 → q1 → q1 → q1", "0, 0, 0, 0", "Допустимо"),
        ("acdeee", "q0 → q1 → q2 → q2 → q3 → q3 → q3", "0, 0, 0, 1, 1, 1", "Допустимо"),
        ("ba", "q0 (нет перехода по b)", "—", "Недопустимо"),
        ("acb", "q0 → q1 → q2 (нет перехода по b)", "0, 0, —", "Недопустимо"),
        ("aeb", "q0 → q1 → q3 (нет перехода по b)", "0, 1, —", "Недопустимо"),
    ]
    table(doc, "Таблица 5 — Траектории и результаты проверки", ["Слово", "Траектория состояний", "Выходы", "Результат"], checks, 9)
    body(doc, "Проверка по трём представлениям даёт одинаковый результат: таблицы и матрица показывают те же переходы, что и граф; все три формы принимают a, abbb и acdeee, а слова ba, acb и aeb отклоняют.")
    body(doc, "Отдельная проверка по таблицам: слово a проходит q0 → q1 с выходом 0 и допустимо; слово ba не имеет перехода по b из q0 и недопустимо. Проверка по графу: ab проходит q0 → q1 → q1 с выходами 0, 0 и допустимо; acb останавливается в q2 без перехода по b и недопустимо. Проверка по матрице: abe проходит q0 → q1 → q1 → q3 с выходами 0, 0, 1 и допустимо; aeb останавливается в q3 без перехода по b и недопустимо.")

    heading(doc, "ВЫВОД")
    body(doc, "Для варианта 20 построен конечный автомат Мили, распознающий язык регулярного выражения a⟨b⟩⟨(c|d)⟩⟨e⟩. Автомат задан множествами X, Q, U, функциями δ и λ, таблицами переходов и выходов, графом и матрицей переходов-выходов.")
    body(doc, "Таблицы удобны для точного перечисления всех переходов, но хуже показывают структуру циклов. Ориентированный граф наглядно показывает последовательность фаз и петли, однако при большом числе символов может стать перегруженным. Матрица переходов-выходов объединяет обе функции и упрощает проверку связей между состояниями, но менее наглядна для чтения последовательности работы.")
    body(doc, "Конечные автоматы применяются для распознавания лексем в компиляторах, проверки форматов, обработки протоколов, управления устройствами и поиска шаблонов в строках. Проверка примеров подтвердила соответствие построенного автомата регулярному выражению, включая нулевое число повторов в каждом цикле.")

    heading(doc, "КОНТРОЛЬНЫЕ ВОПРОСЫ")
    questions = [
        ("1. Дайте определение конечного автомата.", "Конечный автомат — дискретное устройство с конечным множеством состояний, которое обрабатывает входную последовательность символов, переходя между состояниями и, для автомата Мили, формируя выходные символы."),
        ("2. Что такое входной алфавит КНА?", "Входной алфавит X — конечное множество символов, которые могут поступать на вход автомата."),
        ("3. Что такое алфавит состояний КНА?", "Q — конечное множество внутренних состояний, описывающих текущую фазу обработки входа."),
        ("4. Что такое выходной алфавит КНА?", "U — множество символов, которые автомат может выдавать на выходе."),
        ("5. В чём отличие автомата Мили от автомата Мура?", "В автомате Мили выход зависит от текущего состояния и входного символа; в автомате Мура выход зависит только от состояния."),
        ("6. Какие существуют способы задания КНА?", "Таблицами переходов и выходов, ориентированным графом переходов и матрицей переходов-выходов."),
        ("7. Что такое таблица переходов?", "Табличное представление функции δ: для каждой пары состояния и входного символа указывается следующее состояние."),
        ("8. Что такое таблица выходов?", "Табличное представление функции λ: для каждой пары состояния и входного символа указывается выходной символ автомата Мили."),
        ("9. Что такое матрица переходов-выходов?", "Объединённое представление: в ячейке для пары исходного и целевого состояний указаны входные символы и соответствующие им выходы."),
        ("10. Как строится граф переходов?", "Состояния изображаются вершинами, а переходы — направленными дугами с метками вход/выход; начальное состояние отмечается входящей стрелкой, допускающие состояния — двойным кругом."),
        ("11. Что такое регулярное выражение?", "Формальная запись, задающая множество слов над алфавитом с помощью операций объединения, конкатенации и повторения."),
        ("12. Как построить автомат по регулярному выражению?", "Выделить обязательные фрагменты, альтернативы и повторяющиеся части, назначить состояния фазам чтения, задать переходы и циклы, затем проверить граничные слова."),
        ("13. Что означают выходные символы 0 и 1 в автомате-распознавателе?", "В данной работе 0 отмечает чтение символов до завершающей части e*, а 1 — чтение e. Принадлежность полного слова языку определяется достижением допускающего состояния после чтения всего входа."),
        ("14. Как проверить допустимость слова с помощью автомата?", "Начать в q0 и читать символы по очереди. Если переход отсутствует, слово недопустимо; если вход закончился в допускающем состоянии, слово допустимо."),
    ]
    for question, answer in questions:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.keep_with_next = True
        font(p.add_run(question), 12, True)
        body(doc, answer)

    heading(doc, "СПИСОК ЛИТЕРАТУРЫ")
    refs = [
        "1. Алферова З. В. Теория алгоритмов. — М.: Статистика, 1973. — 164 с.",
        "2. Кузнецов О. П., Адельсон-Вельский Г. М. Дискретная математика для инженера. — М.: Энергия, 1980. — 344 с.",
        "3. Хопкрофт Дж., Мотвани Р., Ульман Дж. Введение в теорию автоматов, языков и вычислений. — М.: Вильямс, 2002. — 528 с.",
        "4. Городецкий В. И. Прикладная алгебра и дискретная математика. — МО СССР, 1986. — 200 с.",
        "5. Лабораторная работа № 4 «Исследование алгоритмов задания конечных автоматов». Методические указания. — 9 с.",
    ]
    for ref in refs:
        body(doc, ref)

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
