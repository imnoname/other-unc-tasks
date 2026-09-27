"""Build the editable GUAP report from the official title-page form."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt


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
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def remove_table_rows(table, start_index):
    for row in list(table.rows)[start_index:]:
        table._tbl.remove(row._tr)


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

    for name, size in (("Heading 1", 14), ("Heading 2", 14)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.first_line_indent = Cm(1.25)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(12)
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
        paragraph = doc.paragraphs[idx]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.left_indent = Pt(0)
        paragraph.paragraph_format.first_line_indent = Pt(0)
        paragraph.paragraph_format.right_indent = Pt(0)
    for idx in (0, 1, 7):
        for run in doc.paragraphs[idx].runs:
            set_run_font(run, size=14, bold=(idx == 0))

    teacher_table = doc.tables[0]
    set_cell_text(teacher_table.cell(0, 4), "Скобцов Ю.А.", size=12)
    set_cell_text(teacher_table.cell(1, 4), "инициалы, фамилия", size=10)

    title_table = doc.tables[1]
    set_cell_text(title_table.cell(0, 0), "ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 2", size=13, bold=True)
    set_cell_text(title_table.cell(1, 0), "Оптимизация многомерных функций с помощью генетического алгоритма\nВариант 4", size=11)
    set_cell_text(title_table.cell(2, 0), "по курсу: Эволюционные методы проектирования программно-информационных систем", size=10)
    remove_table_rows(title_table, 3)

    student_table = doc.tables[2]
    for paragraph in student_table.cell(0, 0).paragraphs:
        paragraph.paragraph_format.left_indent = Pt(0)
        paragraph.paragraph_format.first_line_indent = Pt(0)
        paragraph.paragraph_format.right_indent = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        for run in paragraph.runs:
            set_run_font(run, size=12)
    set_cell_text(student_table.cell(0, 1), "4332К", size=12)
    set_cell_text(student_table.cell(0, 5), "Могилатов С.И.", size=12)
    set_cell_text(student_table.cell(1, 3), "подпись, дата", size=10)
    set_cell_text(student_table.cell(1, 5), "инициалы, фамилия", size=10)

    doc.add_page_break()


def add_heading(doc, text, level=1, page_break=True):
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    if page_break:
        paragraph.paragraph_format.page_break_before = True
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if level > 1 else WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    set_run_font(run, size=14, bold=True)
    return paragraph


def add_body(doc, text):
    paragraph = doc.add_paragraph(style="Normal")
    paragraph.paragraph_format.first_line_indent = Cm(1.25)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = paragraph.add_run(text)
    set_run_font(run, size=14)
    return paragraph


def add_bullet(doc, text):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.left_indent = Cm(1.25)
    paragraph.paragraph_format.first_line_indent = Cm(-0.5)
    paragraph.paragraph_format.line_spacing = 1.5
    run = paragraph.add_run(text)
    set_run_font(run, size=14)
    return paragraph


def add_caption(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(text)
    set_run_font(run, size=12)
    return paragraph


def add_image(doc, filename, caption, width_cm=15.5):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.add_run().add_picture(str(RESULTS / filename), width=Cm(width_cm))
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


def add_table(doc, caption, headers, rows, widths=None, font_size=11):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Cm(0)
    run = paragraph.add_run(caption)
    set_run_font(run, size=12, bold=True)
    table = doc.add_table(rows=1, cols=len(headers))
    set_table_borders(table)
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], str(header), size=font_size, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], str(value), size=font_size, align=WD_ALIGN_PARAGRAPH.CENTER)
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
    doc.add_paragraph()
    return table


def load_data():
    summary = json.loads((RESULTS / "results_summary.json").read_text(encoding="utf-8"))
    with (RESULTS / "parameter_sweep.csv").open(encoding="utf-8") as stream:
        sweep = list(csv.DictReader(stream))
    return summary, sweep


def median(rows, key):
    values = sorted(float(row[key]) for row in rows)
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def sweep_rows(sweep, experiment, label):
    values = sorted({float(row["value"]) for row in sweep if row["experiment"] == experiment})
    result = []
    for value in values:
        rows = [row for row in sweep if row["experiment"] == experiment and float(row["value"]) == value]
        result.append((label, value, median(rows, "elapsed_seconds"), median(rows, "generations"), median(rows, "best_value")))
    return result


def add_code_listing(doc, filename):
    add_heading(doc, "Приложение А. Листинг программы", level=1, page_break=True)
    source = (ROOT / filename).read_text(encoding="utf-8")
    for line in source.splitlines():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.5)
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run(line if line else " ")
        set_run_font(run, name="Consolas", size=8.5)


def build():
    doc = Document(str(TEMPLATE))
    configure_document(doc)
    add_title_page(doc)

    contents_heading = doc.add_paragraph()
    contents_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contents_heading.paragraph_format.first_line_indent = Cm(0)
    contents_heading.paragraph_format.space_after = Pt(12)
    contents_run = contents_heading.add_run("СОДЕРЖАНИЕ")
    set_run_font(contents_run, size=14, bold=True)
    toc = doc.add_paragraph()
    toc.paragraph_format.first_line_indent = Cm(0)
    add_toc(toc)

    add_heading(doc, "ВВЕДЕНИЕ", level=1)
    add_body(doc, "Генетические алгоритмы применяются для поиска решений в задачах, где пространство вариантов велико, целевая функция имеет сложную форму или аналитические методы неудобны. В лабораторной работе исследуется вещественный генетический алгоритм для поиска глобального минимума многомерной функции варианта 4.")
    add_body(doc, "Цель работы — реализовать генетический алгоритм для оптимизации перемещенного осевого гиперэллипсоида, исследовать влияние основных параметров алгоритма и сравнить полученные результаты с независимым библиотечным эволюционным оптимизатором.")
    add_body(doc, "В отчете приведены постановка задачи, теоретические сведения, описание операторов, листинг программы, результаты запусков для двух- и трехмерного случаев, графики сходимости и параметрического исследования, а также выводы.")

    add_heading(doc, "1 ЗАДАНИЕ И ПОСТАНОВКА ЗАДАЧИ", level=1)
    add_heading(doc, "1.1 Задание", level=2, page_break=False)
    add_body(doc, "Согласно методическим указаниям необходимо создать программу поиска минимума функции варианта 4, вывести график функции и точки популяции для n=2, исследовать влияние размера популяции и вероятностей кроссовера и мутации, а затем повторить поиск для n=3 и сравнить результаты.")
    add_body(doc, "Вариант 4 — перемещенный осевой гиперэллипсоид. В таблице варианта указаны глобальный минимум f(x)=0 и координаты оптимума x_i=5i. Поэтому в реализации используется согласованная с этими условиями функция:")
    add_body(doc, "f(x) = Σ от i=1 до n [5i · (x_i − 5i)^2].")
    add_body(doc, "Аналитический оптимум имеет вид x*=(5, 10, ..., 5n), а минимальное значение равно f(x*)=0. Для n=2 это точка (5, 10), для n=3 — точка (5, 10, 15). Диапазон поиска выбран [-20; 20] для каждой координаты: он содержит аналитические оптимумы обоих исследуемых размерностей.")
    add_table(doc, "Таблица 1 — Параметры базового запуска", ["Параметр", "Значение"], [
        ("Размерность n", "2 и 3"), ("Размер популяции", "80"), ("Вероятность кроссовера", "0,90"),
        ("Вероятность мутации", "0,08"), ("Кроссовер", "BLX-alpha, alpha=0,5"),
        ("Элитизм", "2 особи"), ("Максимум поколений", "500"), ("Остановка по стабильности", "80 поколений"),
        ("Диапазон генов", "[-20; 20]"),
    ])

    add_heading(doc, "2 ТЕОРЕТИЧЕСКИЕ СВЕДЕНИЯ", level=1)
    add_heading(doc, "2.1 Общая схема генетического алгоритма", level=2, page_break=False)
    add_body(doc, "Генетический алгоритм поддерживает популяцию альтернативных решений. На каждом шаге вычисляется значение целевой функции, более перспективные особи получают преимущество при выборе родителей, а скрещивание и мутация создают новые решения. Такая схема описана в методических указаниях и в учебном пособии Э. Вирсански (1, 2).")
    add_body(doc, "В отличие от двоичного представления, вещественная хромосома непосредственно содержит значения переменных. Поэтому длина хромосомы совпадает с размерностью задачи, а операции кодирования и декодирования не требуются.")
    add_heading(doc, "2.2 Операторы и остановка", level=2, page_break=False)
    add_body(doc, "В программе используется турнирный отбор: из случайно выбранной группы кандидатов в родители попадает особь с наименьшим значением функции. Для вещественных хромосом применяется BLX-alpha кроссовер. Потомок выбирается из расширенного интервала между соответствующими генами родителей. Мутация добавляет к отдельным генам нормальное случайное возмущение, после чего координаты ограничиваются допустимым диапазоном.")
    add_body(doc, "Элитизм сохраняет две лучшие особи при формировании нового поколения. Критерий остановки срабатывает при достижении 500 поколений или после 80 поколений без улучшения. Фиксированные seed обеспечивают воспроизводимость серий экспериментов.")

    add_heading(doc, "3 РЕАЛИЗАЦИЯ И ХОД ВЫПОЛНЕНИЯ", level=1)
    add_heading(doc, "3.1 Структура программы", level=2, page_break=False)
    add_body(doc, "Файл variant4_ga.py содержит функцию целевой задачи, операторы отбора, BLX-alpha кроссовера и мутации, основной цикл run_ga и независимый запуск SciPy differential_evolution. Скрипт run_experiments.py выполняет серии повторных запусков, рассчитывает медианные показатели и создает графики.")
    add_body(doc, "Порядок одного поколения таков: оценить популяцию; обновить лучшую найденную особь; сохранить элиту; многократно выбрать пару родителей; с заданной вероятностью выполнить кроссовер; мутировать потомка; ограничить гены; сформировать новое поколение; увеличить счетчик стабильных поколений.")
    add_heading(doc, "3.2 Результаты базовых запусков", level=2, page_break=False)
    summary, sweep = load_data()
    baseline_rows = []
    for n in (2, 3):
        item = summary["baseline"][str(n)]
        baseline_rows.append((
            n, "Собственный ГА", f"{item['custom_ga_best_value_median']:.1e}",
            f"{item['custom_ga_distance_median']:.1e}", f"{item['custom_ga_generations_median']:.0f}", f"{item['custom_ga_time_median']:.3f}",
        ))
        baseline_rows.append((
            n, "SciPy differential_evolution", f"{item['reference_best_value_median']:.1e}", "—",
            f"{item['reference_generations_median']:.0f}", f"{item['reference_time_median']:.3f}",
        ))
    add_body(doc, "В таблице 2 приведены медианные значения по 10 запускам собственного ГА и 5 запускам независимого метода SciPy. Для собственного ГА дополнительно указано расстояние до аналитического оптимума.")
    add_table(doc, "Таблица 2 — Сравнение результатов для n=2 и n=3", ["n", "Метод", "f", "δ", "ген.", "t, с"], baseline_rows, font_size=9.5)
    add_body(doc, "Собственная реализация для обеих размерностей достигла значения целевой функции порядка 10^-11 и расстояния до аналитической точки порядка 10^-6. При увеличении размерности медианное число поколений увеличилось с 107 до 124, а время запуска — с 0,243 до 0,288 с. Это соответствует росту числа вычисляемых генов и оценок функции.")
    add_image(doc, "surface_n2_population.png", "Рисунок 1 — Поверхность целевой функции и финальная популяция для n=2")
    add_image(doc, "convergence_n2.png", "Рисунок 2 — Сходимость собственного ГА для n=2")

    add_heading(doc, "4 ИССЛЕДОВАНИЕ ПАРАМЕТРОВ", level=1)
    add_heading(doc, "4.1 Влияние размера популяции", level=2, page_break=False)
    add_body(doc, "Размер популяции исследован при значениях 30, 60 и 120 особей. При увеличении популяции время одного запуска закономерно возрастает, поскольку в каждом поколении требуется вычислить целевую функцию для большего числа особей. При этом число поколений и точность изменяются не монотонно: большая популяция дает больше разнообразия, но не всегда уменьшает число поколений на простой выпуклой функции.")
    add_heading(doc, "4.2 Влияние вероятности кроссовера", level=2, page_break=False)
    add_body(doc, "Для вероятности кроссовера рассмотрены значения 0,60, 0,80 и 1,00. На исследуемой функции наилучший компромисс по медианной точности и числу поколений получен при 0,80. Полный кроссовер не дал преимущества по времени, так как увеличивает интенсивность создания новых особей без существенной необходимости для выпуклой задачи.")
    add_heading(doc, "4.3 Влияние вероятности мутации", level=2, page_break=False)
    add_body(doc, "Вероятность мутации изменялась от 0,02 до 0,20. Малое значение ускоряет локальную настройку, но уменьшает разнообразие. Значение 0,20 сохраняет возможность выхода из неудачных областей, однако увеличивает разброс и число поколений. В базовом запуске использовано промежуточное значение 0,08.")
    parameter_rows = []
    parameter_rows.extend(sweep_rows(sweep, "population", "N"))
    parameter_rows.extend(sweep_rows(sweep, "crossover_probability", "p_c"))
    parameter_rows.extend(sweep_rows(sweep, "mutation_probability", "p_m"))
    add_table(doc, "Таблица 3 — Медианные показатели параметрического исследования", ["Фактор", "Значение", "t, с", "ген.", "f"], [
        (factor, f"{value:g}", f"{elapsed:.3f}", f"{generations:.1f}", f"{best:.1e}")
        for factor, value, elapsed, generations, best in parameter_rows
    ], font_size=9.5)
    add_image(doc, "parameter_sweep.png", "Рисунок 3 — Зависимость времени, числа поколений и точности от параметров ГА")

    add_heading(doc, "5 ВЫВОДЫ", level=1)
    add_body(doc, "В ходе лабораторной работы реализован вещественный генетический алгоритм для варианта 4 — перемещенного осевого гиперэллипсоида. Использование функции f(x)=Σ5i(x_i−5i)^2 согласует указанную в методичке точку минимума x_i=5i со значением f(x)=0.")
    add_body(doc, "Для n=2 и n=3 собственная реализация стабильно находила окрестность аналитического минимума. Медианное значение целевой функции составило 1,21·10^-11 для n=2 и 1,69·10^-11 для n=3. Сравнение с независимым эволюционным методом SciPy подтвердило корректность порядка найденных значений.")
    add_body(doc, "Исследование параметров показало ожидаемый рост времени при увеличении размера популяции. Вероятности кроссовера и мутации влияют на баланс между разнообразием и локальной настройкой, поэтому выбор промежуточных значений 0,90 и 0,08 обеспечивает устойчивый результат для данной выпуклой функции.")
    add_body(doc, "Все эксперименты сохранены в CSV и JSON, а исходный код приведен в приложении А. Благодаря фиксированным seed результаты можно воспроизвести повторным запуском run_experiments.py.")

    add_heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", level=1)
    refs = [
        "1. Лабораторная работа № 2. Оптимизация многомерных функций с помощью ГА: методические указания. Приложение 1, вариант 4.",
        "2. Вирсански Э. Генетические алгоритмы на Python / пер. с англ. А. А. Слинкина. — М.: ДМК Пресс, 2020. — 286 с.",
        "3. ГУАП. Для учебного процесса. Нормативная документация ГУАП. — URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 27.09.2026).",
        "4. SciPy documentation. scipy.optimize.differential_evolution. — URL: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html (дата обращения: 27.09.2026).",
    ]
    for ref in refs:
        paragraph = doc.add_paragraph(style="Normal")
        paragraph.paragraph_format.first_line_indent = Cm(1.25)
        run = paragraph.add_run(ref)
        set_run_font(run, size=14)

    add_code_listing(doc, "variant4_ga.py")
    doc.save(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    build()
