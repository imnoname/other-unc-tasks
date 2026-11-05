from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "title_template.docx"
RESULTS = ROOT / "results"
SUMMARY = json.loads((RESULTS / "results_summary.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "report.docx"


def set_run_font(run, name="Times New Roman", size=14, bold=None, italic=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def set_cell_text(cell, text, *, align=WD_ALIGN_PARAGRAPH.CENTER, size=12, bold=None):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.left_indent = Cm(0)
    paragraph.paragraph_format.right_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold)


def set_cell_shading(cell, fill="D9E2F3"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "777777")
        borders.append(element)
    tbl_pr.append(borders)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    value = OxmlElement("w:t")
    value.text = "2"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instruction, separate, value, end):
        run._r.append(element)
    set_run_font(run, size=12)


def add_toc_field(paragraph):
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.15
    run = paragraph.add_run()
    for kind, text in (("begin", None), ("instr", ' TOC \\o "1-2" \\h \\z \\u '), ("separate", None)):
        if kind in ("begin", "separate"):
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    fallback = OxmlElement("w:t")
    fallback.text = "Обновите поле содержания в Microsoft Word"
    run._r.append(fallback)
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(end)


def add_body_paragraph(doc, text, *, bold_lead=None, keep=False):
    p = doc.add_paragraph(style="Normal")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.right_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_together = keep
    if bold_lead and text.startswith(bold_lead):
        lead = p.add_run(bold_lead)
        set_run_font(lead, bold=True)
        tail = p.add_run(text[len(bold_lead):])
        set_run_font(tail)
    else:
        run = p.add_run(text)
        set_run_font(run)
    return p


def add_heading(doc, text, level=1, *, centered=False, page_break=False):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.first_line_indent = Cm(0 if centered else 1.25)
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.right_indent = Cm(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(10 if level == 1 else 6)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.page_break_before = page_break
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_run_font(run, size=14, bold=True)
    p.style.font.name = "Times New Roman"
    p.style.font.size = Pt(14)
    p.style.font.bold = True
    p.style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    return p


def add_table(doc, title, headers, rows, widths=None, cell_size=10.5):
    caption = doc.add_paragraph(style="Normal")
    caption.alignment = WD_ALIGN_PARAGRAPH.LEFT
    caption.paragraph_format.first_line_indent = Cm(0)
    caption.paragraph_format.space_before = Pt(5)
    caption.paragraph_format.space_after = Pt(3)
    caption.paragraph_format.keep_with_next = True
    run = caption.add_run(title)
    set_run_font(run, size=12)
    table = doc.add_table(rows=1, cols=len(headers))
    set_table_borders(table)
    table.autofit = False
    for i, label in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_text(cell, label, size=cell_size, bold=True)
        set_cell_shading(cell)
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], str(value), align=WD_ALIGN_PARAGRAPH.LEFT, size=cell_size)
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.first_line_indent = Cm(0)
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = Pt(1)
    return table


def add_figure(doc, image_path, caption, width_cm=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(image_path), width=Cm(width_cm))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.first_line_indent = Cm(0)
    c.paragraph_format.space_after = Pt(6)
    c.paragraph_format.keep_together = True
    set_run_font(c.add_run(caption), size=12)


def add_code_listing(doc, appendix, title, path):
    add_heading(doc, f"ПРИЛОЖЕНИЕ {appendix}", 1, centered=True, page_break=True)
    add_heading(doc, title, 2, centered=True)
    source = path.read_text(encoding="utf-8").splitlines()
    for line in source:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0)
        p.paragraph_format.right_indent = Cm(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.keep_together = False
        run = p.add_run(line if line else " ")
        set_run_font(run, name="Consolas", size=8)


def main():
    doc = Document(TEMPLATE)
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)
    section.different_first_page_header_footer = True
    section.footer.is_linked_to_previous = False
    add_page_number(section.footer.paragraphs[0])
    section.first_page_footer.paragraphs[0].clear()

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)

    # The official GUAP form supplies the title-page field positions and signature lines.
    doc.paragraphs[1].text = "КАФЕДРА № 43"
    doc.paragraphs[1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    teacher = doc.tables[0]
    set_cell_text(teacher.rows[0].cells[-1], "Скобцов Ю.А.")
    title = doc.tables[1]
    set_cell_text(title.rows[0].cells[0], "ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 6", size=14, bold=True)
    set_cell_text(title.rows[1].cells[0], "Оптимизация путей на графах с помощью муравьиных алгоритмов\nВариант 4", size=12)
    set_cell_text(title.rows[2].cells[0], "по курсу: Эволюционные методы проектирования программно-информационных систем", size=12)
    student = doc.tables[2]
    set_cell_text(student.rows[0].cells[1], "4332")
    set_cell_text(student.rows[0].cells[-1], "Могилатов С.И.")
    doc.paragraphs[-1].text = "Санкт-Петербург 2026"
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()
    toc_heading = doc.add_paragraph()
    toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    toc_heading.paragraph_format.first_line_indent = Cm(0)
    set_run_font(toc_heading.add_run("СОДЕРЖАНИЕ"), size=14, bold=True)
    toc = doc.add_paragraph()
    add_toc_field(toc)

    add_heading(doc, "ВВЕДЕНИЕ", 1, centered=True)
    add_body_paragraph(doc, "Муравьиные алгоритмы применяют для дискретных задач, где решение можно представить последовательностью переходов по графу. В этой работе исследуются два связанных случая на наборе Bayg29: открытый гамильтонов путь, проходящий через каждый город ровно один раз, и замкнутый тур задачи коммивояжёра.")
    add_body_paragraph(doc, "Цель работы — реализовать муравьиный алгоритм для варианта 4, графически показать найденные маршруты и ход сходимости, сопоставить длину тура с эталонным решением, а также оценить влияние числа муравьёв и скорости испарения феромона.")
    add_body_paragraph(doc, "Работа включает постановку задачи, краткое описание алгоритма, воспроизводимые параметры экспериментов, таблицы и графики результатов, сравнение с контрольным туром и ответы на контрольные вопросы. Требования к составу и оформлению отчёта взяты из методических указаний и опубликованных правил ГУАП [1; 2].")

    add_heading(doc, "1 ЗАДАНИЕ И ПОСТАНОВКА ЗАДАЧИ", 1, page_break=True)
    add_heading(doc, "1.1 Индивидуальное задание", 2)
    add_body_paragraph(doc, "Для варианта 4 используется набор Bayg29 — 29 городов Баварии. В первой части требуется найти гамильтонов путь и показать его графически и по этапам поиска. Во второй части требуется решить задачу коммивояжёра, построить цикл и сравнить его с эталонным туром. Методические указания также предлагают сопоставить результат с лабораторной работой № 3 и исследовать влияние вероятностей кроссовера и мутации [1].")
    add_body_paragraph(doc, "Кроссовер и мутация являются операторами генетических алгоритмов и в реализованном муравьином алгоритме не используются. Поэтому экспериментальная часть варьирует параметры, непосредственно управляющие колонией: число муравьёв и коэффициент испарения. В репозитории лабораторная работа № 3 посвящена задаче 0/1-рюкзака, а не маршрутизации Bayg29; длины решений этих разных задач численно несопоставимы. Сравнение с ЛР3 поэтому проводится на уровне принципов поиска, а качество тура — по эталонному циклу Bayg29.")
    add_heading(doc, "1.2 Математическая модель", 2)
    add_body_paragraph(doc, "Каждый город — вершина полного взвешенного графа. Вес ребра между городами i и j равен евклидову расстоянию dᵢⱼ = √((xᵢ − xⱼ)² + (yᵢ − yⱼ)²), рассчитанному по координатам из приложения к методическим указаниям. Маршрут является перестановкой номеров 1–29.")
    add_body_paragraph(doc, "Для открытого пути длина Lп = Σ d(vₖ, vₖ₊₁), k=1…28. Для цикла добавляется ребро возврата: Lц = Lп + d(v₂₉, v₁). Эталонная последовательность Bayg29 задаёт цикл длиной 9074,148. После удаления замыкающего ребра её длина равна 8791,836; это допустимый контрольный открытый путь, но не доказанный оптимум задачи о пути.")
    add_body_paragraph(doc, "Итак, сравниваются две постановки на одной и той же матрице расстояний: путь заканчивается в последнем посещённом городе, а тур включает ещё одно ребро между последним и первым городами.")

    add_heading(doc, "2 КРАТКИЕ ТЕОРЕТИЧЕСКИЕ СВЕДЕНИЯ", 1, page_break=True)
    add_heading(doc, "2.1 Построение маршрута", 2)
    add_body_paragraph(doc, "Муравьиная колония строит множество пробных решений. Каждый муравей начинает в случайном городе и последовательно выбирает ещё не посещённый город, пока не сформирует полную перестановку. Вероятность перехода зависит от накопленного феромона τᵢⱼ и эвристической привлекательности короткого ребра ηᵢⱼ = 1/dᵢⱼ:")
    add_body_paragraph(doc, "pᵢⱼ = τᵢⱼᵅ ηᵢⱼᵝ / Σₗ∈N τᵢₗᵅ ηᵢₗᵝ, где N — множество непосещённых городов. Параметр α задаёт влияние опыта предыдущих муравьёв, а β — предпочтение коротких рёбер. В программе α=1 и β=3.")
    add_heading(doc, "2.2 Испарение и обновление феромона", 2)
    add_body_paragraph(doc, "После построения маршрутов феромон испаряется: τᵢⱼ ← (1−ρ)τᵢⱼ. Затем каждое ребро маршрута получает добавку Δτ = Q/L, где Q — константа, а L — длина найденного маршрута. В реализации обновление симметрично для неориентированных рёбер. Испарение не даёт старым решениям полностью подавить исследование других маршрутов; добавка Q/L усиливает рёбра, входящие в более короткие маршруты.")
    add_heading(doc, "2.3 Случайный поиск и критерий остановки", 2)
    add_body_paragraph(doc, "Алгоритм повторяет построение решений заданное число итераций и сохраняет лучшее найденное решение. После каждой итерации записываются длина лучшего маршрута к текущему моменту и средняя длина маршрутов колонии. Эти данные позволяют просматривать поиск по итерациям в подробном режиме и на графике сходимости.")

    add_heading(doc, "3 АЛГОРИТМ И ПРОГРАММНАЯ РЕАЛИЗАЦИЯ", 1, page_break=True)
    add_heading(doc, "3.1 Последовательность работы программы", 2)
    for text in [
        "1. Загрузить координаты 29 городов Bayg29 и вычислить симметричную матрицу евклидовых расстояний.",
        "2. Инициализировать небольшое одинаковое количество феромона на каждом ребре и создать колонию.",
        "3. Для каждого муравья выбрать случайный начальный город и построить маршрут, каждый город посещая один раз.",
        "4. Рассчитать длину пути или цикла, обновить глобальное лучшее решение и записать показатели итерации.",
        "5. Испарить феромон, добавить Q/L на ребра каждого маршрута и перейти к следующей итерации.",
        "6. Сохранить результаты, изображения маршрутов, график сходимости и CSV параметрического исследования.",
    ]:
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Cm(1.25)
        p.paragraph_format.first_line_indent = Cm(-0.5)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(0)
        set_run_font(p.add_run(text))
    add_body_paragraph(doc, "После каждой итерации сохраняются лучшее и среднее значения длины, а допустимость итогового маршрута проверяется по числу вершин и отсутствию повторов. Исходный код алгоритмического модуля приведён в приложении А, сценарий экспериментов — в приложении Б.")
    add_heading(doc, "3.2 Параметры эксперимента", 2)
    add_body_paragraph(doc, "Базовые серии используют фиксированные начальные значения генератора случайных чисел для повторяемости. Путь и цикл запускаются отдельно; основная серия содержит 40 муравьёв и 200 итераций. Параметрическое исследование выполняет по 120 итераций для каждой комбинации. Настройки двух серий сведены в таблицу 2.")
    add_table(doc, "Таблица 2 — Настройки алгоритма", ["Параметр", "Базовый запуск", "Исследование"], [
        ("Число муравьёв", "40", "20 или 40"), ("Итерации", "200", "120"),
        ("α — влияние феромона", "1,0", "1,0"), ("β — влияние расстояния", "3,0", "3,0"),
        ("Испарение ρ", "0,35", "0,25 или 0,45"), ("Константа Q", "100", "100"),
        ("Начальные значения", "seed 44 (путь), 45 (цикл)", "seed 51–54"),
    ], widths=[4.4, 5.5, 6.1], cell_size=9.5)
    add_heading(doc, "4 РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА", 1, page_break=True)
    path = SUMMARY["base"]["path"]
    cycle = SUMMARY["base"]["cycle"]
    reference_cycle = SUMMARY["reference_cycle_length"]
    reference_path = SUMMARY["reference_open_path_length"]
    path_diff = (path["length"] - reference_path) / reference_path * 100
    cycle_diff = (cycle["length"] - reference_cycle) / reference_cycle * 100
    add_heading(doc, "4.1 Гамильтонов путь", 2)
    add_body_paragraph(doc, "В первой серии найден открытый путь длиной 8403,049. Маршрут проходит через все 29 городов по одному разу и не содержит возвратного ребра. Для ориентира он на " + f"{abs(path_diff):.2f}% короче пути длиной 8791,836, полученного удалением замыкающего ребра из эталонного тура. Такое сравнение показывает качество найденного решения относительно контрольного маршрута, но не доказывает оптимальность открытого пути.")
    add_body_paragraph(doc, "Последовательность посещения: " + " → ".join(map(str, path["route_1based"])) + ". На рисунке 1 показана геометрия найденного пути.")
    add_figure(doc, RESULTS / "bayg29_hamiltonian_path.png", "Рисунок 1 — Найденный гамильтонов путь Bayg29", 15.0)

    add_heading(doc, "4.2 Цикл коммивояжёра", 2)
    add_body_paragraph(doc, "Лучший найденный замкнутый тур имеет длину 9328,340 при эталонном значении 9074,148. Отклонение составляет +" + f"{cycle_diff:.2f}% относительно контрольного тура. Маршрут проходит через каждый город один раз и возвращается в начальный город: " + " → ".join(map(str, cycle["route_1based"])) + f" → {cycle['route_1based'][0]}.")
    add_figure(doc, RESULTS / "bayg29_tsp_cycle.png", "Рисунок 2 — Найденный замкнутый тур Bayg29", 15.0)
    add_body_paragraph(doc, "На рисунке 3 показано изменение лучшей длины по итерациям. Ступенчатые участки означают, что в этой части поиска глобально лучшее решение не изменилось; снижение кривой фиксирует появление более короткого маршрута.")
    add_figure(doc, RESULTS / "convergence.png", "Рисунок 3 — Сходимость алгоритма для пути и цикла", 15.0)
    add_body_paragraph(doc, "Сводные численные показатели обеих серий приведены в таблице 3.")
    add_table(doc, "Таблица 3 — Итоги базовых серий", ["Задача", "Найденная длина", "Контрольная длина", "Разница, %", "Время, с"], [
        ("Открытый путь", f"{path['length']:.3f}", f"{reference_path:.3f} (допустимый путь)", f"{path_diff:+.2f}%", f"{path['elapsed_seconds']:.3f}"),
        ("Замкнутый цикл", f"{cycle['length']:.3f}", f"{reference_cycle:.3f} (эталон)", f"{cycle_diff:+.2f}%", f"{cycle['elapsed_seconds']:.3f}"),
    ], widths=[3.1, 2.8, 4.8, 2.3, 2.0])

    add_heading(doc, "4.3 Влияние параметров колонии", 2)
    add_body_paragraph(doc, "В эксперименте изменялись число муравьёв и коэффициент испарения при одинаковых α, β, Q и числе итераций. Таблица 4 показывает лучшую длину цикла и измеренное время каждой серии. Это исследование параметров муравьиного метода заменяет запрошенную в формулировке методички вариацию кроссовера и мутации, которых в данном алгоритме нет.")
    study_rows = []
    for row in SUMMARY["study"]:
        diff = (row["best_length"] - reference_cycle) / reference_cycle * 100
        study_rows.append((str(row["ants"]), f"{row['evaporation']:.2f}", f"{row['best_length']:.3f}", f"{diff:+.2f}%", f"{row['time_seconds']:.3f}"))
    add_table(doc, "Таблица 4 — Результаты исследования параметров", ["Муравьи", "Испарение ρ", "Лучшая длина", "К эталону", "Время, с"], study_rows,
              widths=[2.2, 2.5, 3.5, 3.0, 2.3])
    add_body_paragraph(doc, "В этой серии 40 муравьёв дали более короткие туры, чем 20 муравьёв, но почти удвоили время расчёта. При 40 муравьях обе проверенные скорости испарения привели к одинаковой лучшей длине; при 20 муравьях значение ρ=0,25 оказалось немного лучше ρ=0,45. Четыре запуска недостаточны для общего вывода о превосходстве одной настройки: стохастический поиск зависит от seed, а измеренное время — от нагрузки компьютера.")

    add_heading(doc, "4.4 Сопоставление с лабораторной работой № 3", 2)
    add_body_paragraph(doc, "В имеющемся отчёте ЛР3 решается задача 0/1-рюкзака генетическим алгоритмом. У неё иной тип решения и другая целевая функция, поэтому сравнивать численные значения целевой функции с длинами туров Bayg29 нельзя. На уровне метода обе работы используют популяционный стохастический поиск и повторное улучшение решений. Генетический алгоритм оперирует хромосомами и генетическими операторами; муравьиный алгоритм строит маршруты и передаёт опыт через феромон. Для количественной оценки ЛР6 использован эталонный цикл Bayg29 из методички.")

    add_heading(doc, "5 ОТВЕТЫ НА КОНТРОЛЬНЫЕ ВОПРОСЫ", 1, page_break=True)
    answers = [
        "Потенциальное решение представляется допустимым маршрутом — последовательностью вершин графа.",
        "Феромон τᵢⱼ отражает накопленный опыт использования ребра; его величина возрастает после прохождения по нему муравьёв.",
        "Испарение уменьшает вклад старых маршрутов и помогает исследовать альтернативы; на ребре τ обновляется умножением на (1−ρ).",
        "В простом муравьином алгоритме агенты строят пути вероятностно, оценивают их длину, испаряют феромон и усиливают рёбра хороших решений.",
        "α управляет влиянием феромона, β — эвристики короткого ребра 1/dᵢⱼ; большие значения сильнее смещают выбор к соответствующей информации.",
        "Качество маршрута для данной задачи оценивается суммарной длиной его рёбер; меньшее значение означает лучшее решение.",
        "Критериями остановки могут быть лимит итераций, приемлемое значение качества или отсутствие улучшения в течение заданного числа итераций.",
        "Основные параметры: число муравьёв, α, β, скорость испарения ρ, константа феромона Q, число итераций и начальный seed.",
        "Общий цикл: инициализация, построение маршрутов, вычисление качества, испарение и добавление феромона, сохранение лучшего результата, проверка останова.",
        "С генетическими алгоритмами муравьиные алгоритмы объединяют популяция решений, случайный поиск и итерационное усиление перспективных вариантов.",
        "Генетический алгоритм изменяет хромосомы отбором, кроссовером и мутацией; муравьиный алгоритм строит решения последовательно, используя эвристику и распределённый феромонный след.",
    ]
    for i, answer in enumerate(answers, 1):
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.line_spacing = 1.2
        p.paragraph_format.space_after = Pt(2)
        set_run_font(p.add_run(f"{i}. "), size=13, bold=True)
        set_run_font(p.add_run(answer), size=13)

    add_heading(doc, "ЗАКЛЮЧЕНИЕ", 1, centered=True, page_break=True)
    add_body_paragraph(doc, "Реализован муравьиный алгоритм для варианта 4 на данных Bayg29. Программа строит допустимый гамильтонов путь и отдельный замкнутый цикл, сохраняет маршруты, графики сходимости, историю эксперимента и сводную таблицу.")
    add_body_paragraph(doc, f"Для открытого пути получена длина {path['length']:.3f}; для цикла — {cycle['length']:.3f}, что на {cycle_diff:.2f}% выше эталонного значения. Исследование параметров показало компромисс между качеством и временем: увеличение колонии с 20 до 40 муравьёв улучшило найденный тур в проверенных сериях, но увеличило расчётное время.")
    add_body_paragraph(doc, "Пошаговую динамику качества можно просмотреть в подробном режиме программы, а её графическое представление — на кривых сходимости. Эталонный тур является контрольной точкой для TSP; удаление его замыкающего ребра используется только как допустимый ориентир для задачи открытого пути. Следующий шаг для более надёжных выводов — повторить параметрические серии на нескольких seed и сравнить распределения длин маршрутов.")

    add_heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", 1, centered=True, page_break=True)
    sources = [
        "Методические указания. Лабораторная работа № 6 «Оптимизация путей на графах с помощью муравьиных алгоритмов». 30 с. (Предоставленный учебный материал).",
        "Санкт-Петербургский государственный университет аэрокосмического приборостроения. Для учебного процесса: правила оформления учебных работ и титульные листы лабораторных работ. URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 05.11.2026).",
        "Лабораторная работа № 3. Решение задачи 0/1-рюкзака генетическим алгоритмом: отчёт, использованный для качественного сопоставления методов. Репозиторий other-unc-tasks, ветка предмета.",
    ]
    for i, source in enumerate(sources, 1):
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.paragraph_format.line_spacing = 1.5
        set_run_font(p.add_run(f"{i}. {source}"))

    add_code_listing(doc, "А", "Модуль муравьиной колонии", ROOT / "ant_colony.py")
    add_code_listing(doc, "Б", "Сценарий экспериментов", ROOT / "run_experiments.py")

    # Keep all cover-page paragraphs and labels free from body indents.
    for p in doc.paragraphs[:8]:
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0)
        p.paragraph_format.right_indent = Cm(0)
    doc.core_properties.title = "Лабораторная работа № 6 — Муравьиный алгоритм Bayg29"
    doc.core_properties.subject = "Эволюционные методы проектирования программно-информационных систем"
    doc.core_properties.author = "Могилатов Семен Игоревич"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
