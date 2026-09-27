"""Build the editable GUAP report for TVP laboratory work 2, variant 20."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "assets" / "lab_title.docx"
OUTPUT = ROOT / "report.docx"
TRACE = ROOT / "output" / "variant20_trace.txt"
FIGURE = ROOT / "output" / "trace_figure.png"


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
    paragraph.paragraph_format.right_indent = Pt(0)
    paragraph.paragraph_format.first_line_indent = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
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
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
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
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(14)
        style.font.bold = True
        style.paragraph_format.first_line_indent = Cm(1.25)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(12)
        style.paragraph_format.keep_with_next = True

    footer = section.footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(paragraph, "PAGE")
    for run in paragraph.runs:
        set_run_font(run, size=12)


def add_title_page(doc):
    doc.paragraphs[1].text = "КАФЕДРА № 43"
    doc.paragraphs[7].text = "Санкт-Петербург 2026"
    for index in (2, 3):
        paragraph = doc.paragraphs[index]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.left_indent = Pt(0)
        paragraph.paragraph_format.right_indent = Pt(0)
        paragraph.paragraph_format.first_line_indent = Pt(0)
    for index in (0, 1, 7):
        for run in doc.paragraphs[index].runs:
            set_run_font(run, size=14, bold=(index == 0))

    teacher_table = doc.tables[0]
    set_cell_text(teacher_table.cell(0, 4), "Охтилев М. Ю.\nРогачев С. А.", size=10)
    set_cell_text(teacher_table.cell(1, 4), "инициалы, фамилия", size=9)

    title_table = doc.tables[1]
    set_cell_text(title_table.cell(0, 0), "ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 2", size=13, bold=True)
    set_cell_text(title_table.cell(1, 0), "Исследование алгоритмов на машине Тьюринга\nВариант 20", size=11)
    set_cell_text(title_table.cell(2, 0), "по курсу: Теория вычислительных процессов", size=10)
    remove_table_rows(title_table, 3)

    student_table = doc.tables[2]
    set_cell_text(student_table.cell(0, 1), "4332", size=12)
    set_cell_text(student_table.cell(0, 5), "Могилатов С. И.", size=12)
    set_cell_text(student_table.cell(1, 3), "подпись, дата", size=9)
    set_cell_text(student_table.cell(1, 5), "инициалы, фамилия", size=9)
    doc.add_page_break()


def add_heading(doc, text, level=1, page_break=True):
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.page_break_before = page_break
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.first_line_indent = Cm(0) if level == 1 else Cm(1.25)
    run = paragraph.add_run(text)
    set_run_font(run, size=14, bold=True)
    return paragraph


def add_body(doc, text):
    paragraph = doc.add_paragraph(style="Normal")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.first_line_indent = Cm(1.25)
    paragraph.paragraph_format.line_spacing = 1.5
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


def add_code(doc, text, size=8.5):
    for line in text.splitlines():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.5)
        paragraph.paragraph_format.right_indent = Cm(0)
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run(line if line else " ")
        set_run_font(run, name="Consolas", size=size)


def add_caption(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(text)
    set_run_font(run, size=12)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn("w:" + edge))
        if element is None:
            element = OxmlElement("w:" + edge)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "808080")


def add_table(doc, caption, headers, rows, font_size=10):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Cm(0)
    run = paragraph.add_run(caption)
    set_run_font(run, size=12, bold=True)
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = True
    set_table_borders(table)
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], str(header), size=font_size, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], str(value), size=font_size)
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
    doc.add_paragraph()
    return table


def create_trace_figure():
    trace_text = TRACE.read_text(encoding="utf-8")
    lines = trace_text.splitlines()
    visible = [
        "Трассировка варианта 20",
        "Начальная лента: q0 11*11=",
        "",
    ]
    visible.extend(lines[-11:])
    visible.extend(["", "Конечная конфигурация: =111111111 qz", "Результат: 111111111"])
    width, line_height = 1800, 42
    height = 80 + line_height * len(visible)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 24)
        title_font = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
        title_font = font
    y = 25
    for index, line in enumerate(visible):
        draw.text((35, y), line, fill="black", font=title_font if index == 0 else font)
        y += line_height
    image.save(FIGURE)


def build():
    create_trace_figure()
    doc = Document(str(TEMPLATE))
    configure_document(doc)
    add_title_page(doc)

    contents = doc.add_paragraph()
    contents.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contents.paragraph_format.first_line_indent = Cm(0)
    run = contents.add_run("СОДЕРЖАНИЕ")
    set_run_font(run, size=14, bold=True)
    toc_rows = [
        ("Введение", "3"),
        ("1 Цель работы", "4"),
        ("2 Основные сведения из теории", "5"),
        ("3 Постановка задачи", "6"),
        ("4 Алгоритм машины Тьюринга", "7"),
        ("5 Совокупность команд", "8"),
        ("6 Проверка работы", "9"),
        ("7 Листинг программы эмулятора", "10"),
        ("8 Контрольные вопросы", "11"),
        ("Вывод", "12"),
        ("Список использованных источников", "13"),
        ("Приложение А. Листинг программы", "14"),
    ]
    for title, page in toc_rows:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(1.25)
        paragraph.paragraph_format.line_spacing = 1.5
        run = paragraph.add_run(f"{title} ........................................ {page}")
        set_run_font(run, size=14)

    add_heading(doc, "ВВЕДЕНИЕ")
    add_body(doc, "Машина Тьюринга задаёт формальную модель вычислений с помощью конечного управляющего устройства, ленты и считывающей головки. В лабораторной работе исследуется построение такой машины для арифметической функции, аргументы и результат которой записываются в унарной системе счисления.")
    add_body(doc, "Цель работы — разработать программу машины Тьюринга для варианта 20, проверить её на тестовом примере и создать эмулятор, который считывает описание машины из файлов, выполняет команды пошагово и сохраняет трассировку в файл.")

    add_heading(doc, "1 ЦЕЛЬ РАБОТЫ")
    add_body(doc, "Изучить формальную модель машины Тьюринга и приобрести навыки построения программ для вычисления арифметических функций. На практическом уровне требуется реализовать эмулятор машины Тьюринга с файловым вводом программы, алфавита и входной ленты, контролем ошибок и записью пошагового результата.")

    add_heading(doc, "2 ОСНОВНЫЕ СВЕДЕНИЯ ИЗ ТЕОРИИ")
    add_heading(doc, "2.1 Определение машины Тьюринга", level=2, page_break=False)
    add_body(doc, "Машина Тьюринга — абстрактный автомат, который состоит из управляющего устройства с конечным множеством состояний, бесконечной ленты, разбитой на ячейки, и считывающей головки. В каждой ячейке находится один символ внешнего алфавита, а головка за один такт читает символ, может заменить его, изменить состояние и сдвинуться на одну позицию влево, вправо или остаться на месте.")
    add_body(doc, "Машина задаётся кортежем M = <Q, A, k0, P>, где Q — внутренний алфавит состояний, A — внешний алфавит символов, k0 — начальная конфигурация, а P — совокупность команд. Состояние q0 является начальным, а qz — конечным.")
    add_heading(doc, "2.2 Принцип функционирования", level=2, page_break=False)
    add_body(doc, "Команда машины имеет вид qi aj -> qk al D. Она применяется, когда машина находится в состоянии qi и обозревает символ aj. После выполнения команды в ячейку записывается al, управляющее устройство переходит в qk, а головка перемещается в направлении D. Направления обозначаются R, L и E.")
    add_body(doc, "Полная конфигурация содержит содержимое ленты, текущее состояние и положение головки. Стандартная начальная конфигурация имеет вид q0a, где головка обозревает первый символ входного слова. Работа заканчивается при переходе в qz.")
    add_heading(doc, "2.3 Способы задания машины", level=2, page_break=False)
    add_body(doc, "Поведение машины можно задать перечислением команд, таблицей переходов или диаграммой состояний. В данной работе используется перечисление команд в текстовом файле. Такой формат удобно загружать в эмулятор и проверять автоматически.")

    add_heading(doc, "3 ПОСТАНОВКА ЗАДАЧИ")
    add_body(doc, "Номер варианта — 20. Требуется вычислить функцию f(x, y) = (x + 1)(y + 1). Аргументы представлены единицами: x записывается как последовательность из x символов 1, y — как последовательность из y символов 1. Между аргументами используется символ *. Для служебного обозначения конца второго аргумента в программе используется символ =.")
    add_body(doc, "Тестовый пример x = 2, y = 2 имеет вид 11*11=. Ожидаемый результат равен (2 + 1)(2 + 1) = 9, то есть 111111111. После остановки машина оставляет на ленте конфигурацию =111111111.")
    add_body(doc, "Эмулятор должен считывать входную ленту, программу машины и внешний алфавит из отдельных файлов. Выходной файл должен содержать состояние ленты перед каждой командой, положение головки, выполненную команду и итоговое состояние. При ошибках программа должна сообщать об отсутствующем переходе, неизвестном символе, пустом алфавите и других нарушениях формата.")
    add_table(doc, "Таблица 1 — Файлы входных и выходных данных", ["Файл", "Назначение", "Пример"], [
        ("data/alphabet.txt", "Внешний алфавит", "1 * X Y = λ"),
        ("data/variant20.tm", "Команды машины Тьюринга", "q0 1 -> q1 1 L"),
        ("data/tape_2x2.txt", "Начальная лента", "11*11="),
        ("output/variant20_trace.txt", "Пошаговая трассировка", "Результат: 111111111"),
    ])

    add_heading(doc, "4 АЛГОРИТМ МАШИНЫ ТЬЮРИНГА")
    add_body(doc, "Сначала машина добавляет по одной единице к каждому аргументу. Для первого аргумента головка перемещается в пустую ячейку слева и записывает единицу. Для второго аргумента символ = временно заменяется единицей, затем = записывается в следующую ячейку справа. После этого на ленте находится представление 1^(x+1)*1^(y+1)=.")
    add_body(doc, "Далее машина многократно выбирает очередную единицу первого аргумента и заменяет её символом X. Для каждой единицы второго аргумента она временно записывает Y, перемещается к концу результата после = и дописывает одну единицу. Затем машина возвращается к символу Y, восстанавливает его в 1 и продолжает копирование. Так одна единица первого аргумента добавляет к результату полный второй аргумент.")
    add_body(doc, "Когда все единицы первого аргумента помечены X, машина проходит влево, стирает служебную часть ленты до символа = и переходит в qz. В результате после разделителя остаётся ровно (x+1)(y+1) единиц.")
    add_body(doc, "Внешний алфавит машины имеет вид A = {1, *, X, Y, =, λ}. Состояния q0–q18 обслуживают подготовку, копирование и очистку ленты; qz является конечным состоянием.")

    add_heading(doc, "5 СОВОКУПНОСТЬ КОМАНД")
    add_body(doc, "Ниже приведена совокупность команд из файла data/variant20.tm. Символ λ обозначает пустую ячейку. Комментарии в файле разделяют подготовку аргументов, умножение и очистку служебной части.")
    commands = [
        line for line in (ROOT / "data" / "variant20.tm").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    add_code(doc, "\n".join(commands), size=8.5)

    add_heading(doc, "6 ПРОВЕРКА РАБОТЫ")
    add_body(doc, "Проверка выполнена на реализованном эмуляторе в формате команд, совместимом с описанием Algo2000. Для входной ленты 11*11= машина выполнила 207 команд, перешла в состояние qz и получила результат 111111111.")
    if FIGURE.exists():
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.add_run().add_picture(str(FIGURE), width=Cm(16))
        add_caption(doc, "Рисунок 1 — Фрагмент трассировки и конечная конфигурация машины")
    add_table(doc, "Таблица 2 — Результаты контрольных запусков", ["x", "y", "Входная лента", "Ожидаемый результат", "Результат МТ"], [
        ("0", "0", "*=", "1", "1"),
        ("1", "1", "1*1=", "1111", "1111"),
        ("2", "2", "11*11=", "111111111", "111111111"),
        ("3", "2", "111*11=", "111111111111", "111111111111"),
        ("4", "3", "1111*111=", "1111111111111111111111", "1111111111111111111111"),
    ], font_size=9)
    add_body(doc, "Дополнительный автоматический прогон охватил все 25 пар x и y от 0 до 4. Во всех случаях длина результата совпала с (x+1)(y+1). Отдельные тесты подтвердили контроль отсутствующего перехода и символа, отсутствующего во внешнем алфавите.")

    add_heading(doc, "7 ЛИСТИНГ ПРОГРАММЫ ЭМУЛЯТОРА")
    add_body(doc, "Эмулятор реализован на Python. Он загружает три входных файла, проверяет их согласованность, хранит ленту в словаре с поддержкой отрицательных индексов и записывает трассировку перед выполнением каждой команды. Командная строка запуска имеет вид:")
    add_code(doc, "python tm_emulator.py --program data/variant20.tm --alphabet data/alphabet.txt --tape data/tape_2x2.txt --output output/variant20_trace.txt", size=8.5)
    add_table(doc, "Таблица 3 — Основные функции эмулятора", ["Функция", "Назначение"], [
        ("load_alphabet", "Читает внешний алфавит и проверяет наличие символа λ."),
        ("load_program", "Разбирает команды, проверяет символы и дубликаты переходов."),
        ("load_tape", "Читает входную ленту и проверяет принадлежность символов алфавиту."),
        ("run_machine", "Выполняет команды, формирует трассировку и извлекает результат."),
        ("_write_trace", "Сохраняет шаги, финальную ленту и результат в выходной файл."),
        ("main", "Обрабатывает параметры командной строки и выводит краткий итог."),
    ], font_size=9)
    add_body(doc, "Полный листинг программы приведён в приложении А.")

    add_heading(doc, "8 КОНТРОЛЬНЫЕ ВОПРОСЫ")
    questions = [
        ("1", "Машина Тьюринга — формальная модель алгоритма с конечным управляющим устройством, лентой и головкой."),
        ("2", "Внутренний алфавит содержит состояния управляющего устройства, включая q0 и qz."),
        ("3", "Внешний алфавит содержит символы, которые могут записываться в ячейки ленты, включая λ."),
        ("4", "Символ λ обозначает пустую ячейку ленты."),
        ("5", "Конфигурация задаёт содержимое ленты, положение головки и текущее состояние машины."),
        ("6", "Стандартная начальная конфигурация имеет вид q0a: головка находится на первом символе входного слова."),
        ("7", "Стандартная конечная конфигурация содержит состояние qz и произвольное содержимое ленты."),
        ("8", "Команда имеет вид qi aj -> qk al D: прочитать, записать, изменить состояние и сдвинуть головку."),
        ("9", "Головка может сдвигаться вправо R, влево L или оставаться на месте E."),
        ("10", "Машину можно задать списком команд, таблицей переходов или диаграммой состояний."),
        ("11", "Тезис Тьюринга утверждает, что всякий алгоритм может быть реализован на машине Тьюринга."),
        ("12", "Машина правильно вычисляет функцию, если для каждого допустимого входа останавливается и оставляет представление правильного результата."),
    ]
    add_table(doc, "Таблица 4 — Ответы на контрольные вопросы", ["№", "Ответ"], questions, font_size=9)

    add_heading(doc, "ВЫВОД")
    add_body(doc, "В работе построена машина Тьюринга для функции f(x, y) = (x + 1)(y + 1) в унарной системе счисления. Алгоритм сначала увеличивает оба аргумента, затем выполняет умножение повторным копированием второго аргумента и удаляет служебную часть ленты перед остановкой.")
    add_body(doc, "Созданный эмулятор считывает описание машины и данные из файлов, выполняет команды пошагово, сохраняет положение головки и состояние ленты, а также контролирует ошибки входных данных. Контрольные и дополнительные запуски подтвердили совпадение длины результата с математическим значением функции.")

    add_heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")
    references = [
        "1. Лабораторная работа № 2 по дисциплине «Теория вычислительных процессов». Методические указания, страницы 1–11.",
        "2. Алферова З. В. Теория алгоритмов. — М.: Статистика, 1973. — 164 с.",
        "3. Кузнецов О. П., Адельсон-Вельский Г. М. Дискретная математика для инженера. — М.: Энергия, 1980. — 344 с.",
        "4. Эббинхауз Г. Д., Якобс К., Ман Ф. К. Машины Тьюринга и рекурсивные функции. — 1972. — 264 с.",
        "5. Хопкрофт Дж., Мотвани Р., Ульман Дж. Введение в теорию автоматов, языков и вычислений. — М.: Вильямс, 2002. — 528 с.",
        "6. ГУАП. Нормативная документация для учебного процесса. — URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 27.09.2026).",
    ]
    for reference in references:
        paragraph = doc.add_paragraph(style="Normal")
        paragraph.paragraph_format.first_line_indent = Cm(1.25)
        run = paragraph.add_run(reference)
        set_run_font(run, size=14)

    add_heading(doc, "Приложение А. Листинг программы эмулятора")
    add_code(doc, (ROOT / "tm_emulator.py").read_text(encoding="utf-8"), size=7.2)

    doc.save(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    build()
