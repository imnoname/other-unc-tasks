"""Build the editable GUAP report for laboratory work 4."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parent
TEMPLATE = Path(r"C:\Users\theju\OneDrive\Документы\ChatGPT\учеба\_guap_refs\lab_title.docx")
OUTPUT = ROOT / "report.docx"
RESULTS = ROOT / "results"


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


def clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def set_cell_text(cell, text, size=12, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.left_indent = Pt(0)
    paragraph.paragraph_format.first_line_indent = Pt(0)
    paragraph.paragraph_format.right_indent = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(str(text))
    set_run_font(run, size=size, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_field(paragraph, instruction):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])


def add_toc(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "Обновите поле содержания в Word"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])


def configure_document(doc):
    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)
    section.different_first_page_header_footer = True
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(14)
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_after = Pt(0)
    for name in ("Heading 1", "Heading 2"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(14)
        style.font.bold = True
        style.paragraph_format.first_line_indent = Cm(1.25)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(10)
        style.paragraph_format.keep_with_next = True
    footer = section.footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    clear_paragraph(paragraph)
    add_field(paragraph, "PAGE")
    for run in paragraph.runs:
        set_run_font(run, size=12)


def add_title_page(doc):
    doc.paragraphs[1].text = "КАФЕДРА № 43"
    doc.paragraphs[7].text = "Санкт-Петербург 2026"
    for idx in (2, 3):
        p = doc.paragraphs[idx]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.left_indent = Pt(0)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.right_indent = Pt(0)
    for idx in (0, 1, 7):
        for run in doc.paragraphs[idx].runs:
            set_run_font(run, size=14, bold=(idx == 0))
    teacher = doc.tables[0]
    set_cell_text(teacher.cell(0, 4), "Скобцов Ю.А.", size=12)
    set_cell_text(teacher.cell(1, 4), "инициалы, фамилия", size=10)
    title = doc.tables[1]
    set_cell_text(title.cell(0, 0), "ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 4", size=13, bold=True)
    set_cell_text(title.cell(1, 0), "Генетическое программирование в задаче символьной регрессии\nВариант 4", size=10)
    set_cell_text(title.cell(2, 0), "по курсу: Эволюционные методы проектирования программно-информационных систем", size=10)
    for row in list(title.rows)[3:]:
        title._tbl.remove(row._tr)
    student = doc.tables[2]
    set_cell_text(student.cell(0, 1), "4332К", size=12)
    set_cell_text(student.cell(0, 5), "Могилатов С.И.", size=12)
    set_cell_text(student.cell(1, 3), "подпись, дата", size=10)
    set_cell_text(student.cell(1, 5), "инициалы, фамилия", size=10)
    doc.add_page_break()


def add_heading(doc, text, level=1, page_break=True):
    p = doc.add_paragraph(style=f"Heading {level}")
    if page_break:
        p.paragraph_format.page_break_before = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_run_font(run, size=14, bold=True)
    return p


def add_body(doc, text):
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.line_spacing = 1.5
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    set_run_font(run, size=14)
    return p


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    set_run_font(run, size=12)


def add_image(doc, filename, caption, width_cm=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.add_run().add_picture(str(RESULTS / filename), width=Cm(width_cm))
    add_caption(doc, caption)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "808080")


def add_table(doc, caption, headers, rows, font_size=10):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(caption)
    set_run_font(run, size=12, bold=True)
    table = doc.add_table(rows=1, cols=len(headers))
    set_table_borders(table)
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, size=font_size, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value, size=font_size)
    doc.add_paragraph()
    return table


def add_code_listing(doc, filename, title):
    add_heading(doc, title, level=1, page_break=True)
    for line in (ROOT / filename).read_text(encoding="utf-8").splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        set_run_font(p.add_run(line or " "), name="Consolas", size=8.5)


def load_results():
    summary = json.loads((RESULTS / "results_summary.json").read_text(encoding="utf-8"))
    with (RESULTS / "parameter_study.csv").open(encoding="utf-8") as stream:
        study = list(csv.DictReader(stream))
    return summary, study


def build():
    doc = Document(str(TEMPLATE))
    configure_document(doc)
    add_title_page(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    set_run_font(p.add_run("СОДЕРЖАНИЕ"), size=14, bold=True)
    toc = doc.add_paragraph()
    toc.paragraph_format.first_line_indent = Cm(0)
    add_toc(toc)
    summary, study = load_results()
    base = summary["problems"]["baseline"]

    add_heading(doc, "ВВЕДЕНИЕ")
    add_body(doc, "Генетическое программирование позволяет искать структуру программы как решение задачи оптимизации. В символьной регрессии программа представляется математическим выражением, а ее качество определяется близостью вычисленных значений к наблюдаемым данным.")
    add_body(doc, "Цель работы - реализовать древовидный генетический алгоритм для восстановления функции варианта 4, исследовать сходимость и влияние параметров, представить лучшие программные деревья графически и сравнить найденную формулу с исходной.")

    add_heading(doc, "1 ЗАДАНИЕ И ПОСТАНОВКА ЗАДАЧИ")
    add_heading(doc, "1.1 Индивидуальное задание", 2, False)
    add_body(doc, "Для варианта 4 требуется найти методом символьной регрессии функцию f(x) = x^6 - 2*x^4 + x^2 по 20 случайным точкам области x ∈ [-1, 1]. Структура программы - древовидное представление. Необходимо задать терминальное и функциональное множества, выбрать фитнесс-функцию, выполнить эволюцию, показать деревья и формулы, сравнить исходную и найденную функции, а также ответить на контрольный вопрос 4.")
    add_table(doc, "Таблица 1 - Параметры индивидуального задания", ["Показатель", "Значение"], [("Вариант", "4"), ("Целевая функция", "x^6 - 2*x^4 + x^2"), ("Область", "[-1, 1]"), ("Обучающее множество", "20 случайных точек"), ("Представление", "древовидное"), ("Контрольный вопрос", "4")])
    add_heading(doc, "1.2 Математическая постановка", 2, False)
    add_body(doc, "Пусть X = {(x_i, y_i)} - обучающее множество, где y_i = f(x_i). Каждая особь p задает вычислимую программу p(x). Требуется минимизировать среднеквадратичную ошибку MSE(p) = (1/N) sum_i (p(x_i) - y_i)^2. Для предотвращения неоправданно больших деревьев в оценку добавляется небольшой штраф, пропорциональный числу узлов.")

    add_heading(doc, "2 КРАТКИЕ ТЕОРЕТИЧЕСКИЕ СВЕДЕНИЯ")
    add_heading(doc, "2.1 Представление программы деревом", 2, False)
    add_body(doc, "В древовидном представлении листья содержат терминалы: переменную x и константы, а внутренние вершины - операции из функционального множества. Арность операции определяет число дочерних узлов. Например, выражение x^6 - 2*x^4 + x^2 представляется деревом, в котором корневой оператор сложения объединяет разность x^6 - 2*x^4 и слагаемое x^2.")
    add_heading(doc, "2.2 Инициализация и операторы", 2, False)
    add_body(doc, "Начальная популяция создается комбинацией методов full и grow. При турнирном отборе из случайной группы выбирается особь с минимальной оценкой. Кроссовер обменивает случайные поддеревья двух родителей, а мутация заменяет случайное поддерево новым. Элитизм переносит лучшую особь в следующее поколение.")
    add_heading(doc, "2.3 Безопасная интерпретация", 2, False)
    add_body(doc, "В алгоритме используются защищенное деление, ограничение аргумента экспоненты и ограничение показателя степени. Нечисловые результаты и переполнение получают штраф. Операции pow2, pow4 и pow6 являются безопасными частными случаями возведения в целую степень и позволяют компактно описывать полиномы.")

    add_heading(doc, "3 ПРОГРАММА И РЕЗУЛЬТАТЫ")
    add_heading(doc, "3.1 Реализация алгоритма", 2, False)
    add_body(doc, "В файле gp_symbolic_regression.py реализованы узел дерева Node, рекурсивная интерпретация, печать формулы, генерация начальной популяции, турнирный отбор, кроссовер поддеревьев, мутация и основной цикл. Сценарий run_experiments.py фиксирует seed 4, создает данные, запускает базовую серию и параметрическое исследование, сохраняет JSON/CSV и изображения.")
    add_body(doc, "В базовом запуске использованы популяция 500 особей, 150 поколений, максимальная глубина 7, вероятность кроссовера 0,85, вероятность мутации 0,12, размер турнира 5 и коэффициент парсимонии 10^-5.")
    add_table(doc, "Таблица 2 - Параметры базового запуска", ["Параметр", "Значение"], [("Размер популяции", "500"), ("Число поколений", "150"), ("Максимальная глубина", "7"), ("Кроссовер", "0,85"), ("Мутация", "0,12"), ("Турнир", "5 особей"), ("Seed", "4")])
    add_heading(doc, "3.2 Результат символьной регрессии", 2, False)
    add_body(doc, "В базовом запуске найдено выражение: " + base["formula"] + ". Среднеквадратичная ошибка на 20 обучающих точках составила " + f"{base['mse']:.8f}" + ", корень из ошибки - " + f"{base['rmse']:.6f}" + ". Дерево содержит " + str(base["size"]) + " узлов и имеет глубину " + str(base["depth"]) + ". Полученная формула является приближением исходной функции; различие оценивается численно и показано на графике.")
    add_image(doc, "convergence.png", "Рисунок 1 - Сходимость генетического программирования")
    add_image(doc, "function_comparison.png", "Рисунок 2 - Сравнение исходной и найденной функций")
    add_heading(doc, "3.3 Графическое представление деревьев", 2, False)
    add_body(doc, "Для контроля эволюции сохранены лучшие деревья поколений 0, 10, 25, 50, 100 и 150. На каждом узле показана операция или терминал, а заголовок содержит формулу соответствующей лучшей особи. Внутри программы дерево сохраняется для каждого поколения, а в отчет включена компактная сводная иллюстрация контрольных итераций.")
    add_image(doc, "tree_progress.png", "Рисунок 3 - Изменение лучшего программного дерева")
    add_heading(doc, "3.4 Параметрическое исследование", 2, False)
    add_body(doc, "Для исследования влияния параметров отдельно изменялись размер популяции, вероятность кроссовера и вероятность мутации. Остальные настройки сохранялись базовыми, а seed сдвигался на номер серии. Чем меньше MSE, тем ближе найденная программа к заданной функции.")
    rows = [(row["factor"], row["value"], f"{float(row['mse']):.6f}", f"{float(row['rmse']):.5f}", row["size"], row["time_seconds"]) for row in study]
    add_table(doc, "Таблица 3 - Результаты параметрического исследования", ["Фактор", "Значение", "MSE", "RMSE", "Узлы", "Время, с"], rows, font_size=9)
    add_body(doc, "Наиболее низкая ошибка среди серий получена при увеличенной популяции 750 особей. Уменьшение вероятности кроссовера ухудшило результат, поскольку обмен генетическим материалом происходил реже. Изменение вероятности мутации повлияло на баланс между сохранением удачных поддеревьев и исследованием новых структур.")

    add_heading(doc, "4 ВЫВОДЫ")
    add_body(doc, "В работе реализован генетический алгоритм в режиме генетического программирования для символьной регрессии. Использовано древовидное представление программ, терминальное множество переменной x и целых констант от -5 до 5, а также функциональное множество арифметических и безопасных математических операций.")
    add_body(doc, "На 20 псевдоэкспериментальных точках функция была приближена с воспроизводимой среднеквадратичной ошибкой 0,00011744 в базовой серии. График сравнения показывает согласованное поведение найденной и исходной функций на области [-1, 1]. Параметрический эксперимент подтвердил, что увеличение популяции обычно повышает разнообразие поиска, но требует больше времени.")

    add_heading(doc, "5 ОТВЕТ НА КОНТРОЛЬНЫЙ ВОПРОС")
    add_body(doc, "Линейное представление программы - это хранение программы в виде последовательности терминалов и функций. Для однозначной интерпретации каждой функции задается арность. Наиболее распространены префиксная, инфиксная и постфиксная записи. В постфиксном варианте выражение читается слева направо с использованием стека: терминал помещается в стек, а операция извлекает из него нужное число аргументов и помещает результат обратно. Например, x x 2 pow4 * - можно интерпретировать как x - 2*x^4.")
    add_body(doc, "Преимущество линейного представления состоит в компактности, простоте сериализации и удобстве последовательного обхода. Недостаток заключается в необходимости контролировать корректность последовательности: после мутации может нарушиться баланс стека, арность операции или ограничение длины программы. В древовидном представлении структура корректна по построению, а обмен поддеревьями наглядно реализует кроссовер; линейная форма обычно проще для хранения, но сложнее для сохранения синтаксической корректности.")

    add_heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")
    refs = [
        "1. Лабораторная работа № 4. Генетическое программирование: методические указания.",
        "2. Вирсански Э. Генетические алгоритмы на Python / пер. с англ. - М.: ДМК Пресс, 2020.",
        "3. Скобцов Ю. А. Вычислительный интеллект. - СПб.: ГУАП, 2022.",
        "4. GUAP. Нормативная документация для учебного процесса. - URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 15.10.2026).",
    ]
    for ref in refs:
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.first_line_indent = Cm(1.25)
        set_run_font(p.add_run(ref), size=14)
    add_code_listing(doc, "gp_symbolic_regression.py", "Приложение А. Листинг алгоритма")
    add_code_listing(doc, "run_experiments.py", "Приложение Б. Сценарий экспериментов")
    doc.save(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    build()

