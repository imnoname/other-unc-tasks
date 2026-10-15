"""Сборка отчёта ГУАП по лабораторной работе № 3, вариант 20."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT.parent / "лр 2" / "assets" / "lab_title.docx"
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


def clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def add_page_field(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])


def set_cell_text(cell, text, size=11, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.left_indent = Pt(0)
    paragraph.paragraph_format.right_indent = Pt(0)
    paragraph.paragraph_format.first_line_indent = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(str(text))
    set_run_font(run, size=size, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def remove_table_rows(table, start_index):
    for row in list(table.rows)[start_index:]:
        table._tbl.remove(row._tr)


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
    add_page_field(paragraph)
    for run in paragraph.runs:
        set_run_font(run, size=12)


def add_title_page(doc):
    doc.paragraphs[1].text = "КАФЕДРА № 43"
    doc.paragraphs[7].text = "Санкт-Петербург 2026"
    for index in (2, 3):
        paragraph = doc.paragraphs[index]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.first_line_indent = Pt(0)
    for index in (0, 1, 7):
        for run in doc.paragraphs[index].runs:
            set_run_font(run, size=14, bold=(index == 0))

    teacher_table = doc.tables[0]
    set_cell_text(teacher_table.cell(0, 4), "Рогачев С. А.", size=10)
    set_cell_text(teacher_table.cell(1, 4), "инициалы, фамилия", size=9)

    title_table = doc.tables[1]
    set_cell_text(title_table.cell(0, 0), "ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 3", size=13, bold=True)
    set_cell_text(title_table.cell(1, 0), "Исследование формальной системы Поста\nВариант 20", size=11)
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


def add_code(doc, text, size=8.2):
    for line in text.splitlines():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.5)
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run(line if line else " ")
        set_run_font(run, name="Consolas", size=size)


def add_table(doc, caption, headers, rows, font_size=10):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Cm(0)
    run = paragraph.add_run(caption)
    set_run_font(run, size=12, bold=True)
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = True
    set_table_borders(table)
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, size=font_size, bold=True)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value, size=font_size)
    doc.add_paragraph()
    return table


def build():
    trace = (ROOT / "output" / "variant20_result.txt").read_text(encoding="utf-8")
    source = (ROOT / "posta_emulator.py").read_text(encoding="utf-8")
    doc = Document(str(TEMPLATE))
    configure_document(doc)
    add_title_page(doc)

    add_heading(doc, "СОДЕРЖАНИЕ")
    contents = [
        ("1 Цель работы", "3"),
        ("2 Теоретическая часть", "4"),
        ("3 Постановка задачи", "5"),
        ("4 Построенная формальная система Поста", "6"),
        ("5 Программа-эмулятор", "7"),
        ("6 Результаты выполнения", "8"),
        ("7 Контрольные вопросы", "9"),
        ("Вывод", "10"),
        ("Список использованных источников", "11"),
        ("Приложение А. Листинг программы", "12"),
    ]
    for title, page in contents:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(1.25)
        paragraph.paragraph_format.first_line_indent = Cm(0)
        run = paragraph.add_run(f"{title} ........................................ {page}")
        set_run_font(run, size=14)

    add_heading(doc, "1 ЦЕЛЬ РАБОТЫ")
    add_body(doc, "Изучить формальную систему Поста и освоить построение продукций для вычисления арифметической функции в унарной системе счисления. Разработать эмулятор канонической системы Поста, считывающий описание системы из файла, выполняющий продукционные правила пошагово и сохраняющий протокол вычисления.")

    add_heading(doc, "2 ТЕОРЕТИЧЕСКАЯ ЧАСТЬ")
    add_heading(doc, "2.1 Формальная система", level=2, page_break=False)
    add_body(doc, "Формальная система задаётся внешним алфавитом, множеством переменных, множеством аксиом и правилами вывода. Внешний алфавит содержит символы, которые непосредственно появляются в словах системы. Переменные обозначают произвольные слова над внешним алфавитом и позволяют задавать правило в общем виде.")
    add_body(doc, "Каноническая система Поста использует продукции вида u → v, где левая часть u содержит константы и переменные, а правая часть v задаёт слово, получаемое после подстановки значений переменных. На каждом шаге выбирается применимая продукция, выполняется сопоставление левой части с текущим словом и строится новое слово.")
    add_heading(doc, "2.2 Условия применимости продукций", level=2, page_break=False)
    add_body(doc, "Продукция применима, если для её переменных существует подстановка, при которой левая часть полностью совпадает с текущим словом. После подстановки переменных в правую часть получается следующее слово. Вычисление заканчивается, когда ни одна продукция не применима. Для построенной системы конечное слово имеет вид =1ⁿ, где n — искомый результат.")
    add_body(doc, "В программе используется унарное представление: слово из n символов 1 представляет число n. Поэтому умножение реализуется повторным добавлением копий второго множителя к результирующей части слова.")

    add_heading(doc, "3 ПОСТАНОВКА ЗАДАЧИ")
    add_body(doc, "Вариант 20: f(x, y) = (x + 1)(y + 1). Аргументы x и y записываются последовательностями символов 1 и разделяются символом /. Справа от символа = система накапливает результат. Для контрольного запуска выбраны x = 2 и y = 2, поэтому исходная аксиома имеет вид 11/11=, а ожидаемый результат равен 9.")
    add_body(doc, "Программа должна читать все входные данные из одного текстового файла, отображать последовательность применения продукций в выходном файле и сообщать об ошибках. В частности, контролируются символы, отсутствующие во внешнем алфавите A, и переменные, отсутствующие в множестве X.")
    add_table(doc, "Таблица 1 — Формат файлов лабораторной работы", ["Файл", "Назначение", "Пример"], [
        ("data/variant20.fs", "Описание A, X, A1 и R", "A = {1, /, =, P, Q, L, R}"),
        ("output/variant20_result.txt", "Пошаговый протокол", "Результат: 111111111"),
        ("report.docx", "Оформленный отчёт", "настоящий документ"),
    ])

    add_heading(doc, "4 ПОСТРОЕННАЯ ФОРМАЛЬНАЯ СИСТЕМА ПОСТА")
    add_body(doc, "Для варианта 20 построена система FSₚ = (A, X, A₁, R). Знаки P и Q обозначают фазу подготовки множителей, а L и R — состояние после увеличения аргументов и перед умножением. Переменная c хранит уже накопленный результат.")
    add_table(doc, "Таблица 2 — Компоненты формальной системы", ["Обозначение", "Содержание"], [
        ("A", "{1, /, =, P, Q, L, R}"),
        ("X", "{a, b, c}"),
        ("A₁", "{11/11=}"),
        ("Начальное слово", "11/11="),
        ("Конечная форма", "=1ⁿ"),
    ], font_size=10)
    add_table(doc, "Таблица 3 — Множество продукций R", ["№", "Продукция", "Назначение"], [
        ("1", "a/b= → Pa/Qb=", "Пометить начало фазы увеличения обоих множителей"),
        ("2", "Pa/Qb= → La1/Rb1=", "Добавить по одной единице к x и y"),
        ("3", "La1/Rb=c → La/Rb=cb", "За одну единицу первого множителя добавить копию b"),
        ("4", "L/Rb=c → =c", "Удалить служебные маркеры и исходный второй множитель"),
    ], font_size=9)
    add_body(doc, "Для аксиомы 11/11= правило 1 даёт P11/Q11=. Правило 2 формирует L111/R111=. Три применения правила 3 последовательно дописывают по три единицы: L11/R111=111, L1/R111=111111 и L/R111=111111111. Последнее правило переводит слово в конечную форму =111111111.")

    add_heading(doc, "5 ПРОГРАММА-ЭМУЛЯТОР")
    add_body(doc, "Эмулятор реализован на Python в файле posta_emulator.py. Парсер разбирает множества A, X, A1 и продукции R. Сопоставление левой части выполняется с подстановкой переменных, принимающих унарные слова, включая пустое слово. На каждом шаге выбирается первая применимая продукция.")
    add_body(doc, "Запуск программы выполняется командой:")
    add_code(doc, "python posta_emulator.py --input data/variant20.fs --output output/variant20_result.txt", size=9)
    add_table(doc, "Таблица 4 — Основные функции программы", ["Элемент", "Назначение"], [
        ("parse_system", "Читает описание системы и проверяет A, X, A1, R"),
        ("_match", "Проверяет полное сопоставление продукции со словом"),
        ("_substitute", "Подставляет значения переменных в правую часть"),
        ("run_system", "Выполняет систему и формирует трассировку"),
        ("main", "Обрабатывает параметры запуска и выводит итог"),
    ], font_size=9)
    add_body(doc, "При обнаружении неизвестного символа программа формирует сообщение «Символ ... отсутствует во внешнем алфавите». При неизвестной переменной формируется сообщение о её отсутствии в множестве X.")

    add_heading(doc, "6 РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ")
    add_body(doc, "Тестовый запуск для аксиомы 11/11= завершился успешно. Полученная строка =111111111 содержит девять единиц после знака равенства, что совпадает с f(2, 2) = (2 + 1)(2 + 1) = 9.")
    add_table(doc, "Таблица 5 — Результаты корректных запусков", ["Аксиома", "Ожидаемый результат", "Фактический результат", "Шагов"], [
        ("11/11=", "111111111", "111111111", "6"),
        ("111/11=", "111111111111", "111111111111", "7"),
    ], font_size=9)
    add_body(doc, "В таблице 6 приведены результаты проверки обработки ошибок. Проверки выполнены тестами pytest и подтверждают, что программа не продолжает вычисление при нарушении описания системы.")
    add_table(doc, "Таблица 6 — Проверка ошибочных входных данных", ["Ситуация", "Пример", "Сообщение"], [
        ("Символ вне A", "11/21=", "Символ '2' отсутствует во внешнем алфавите"),
        ("Переменная вне X", "Ld1/Rb=c", "Переменная 'd' отсутствует в множестве X"),
    ], font_size=9)
    add_body(doc, "Фрагмент протокола выполнения для основного запуска:")
    add_code(doc, "\n".join(trace.splitlines()[:33]), size=7.6)

    add_heading(doc, "7 КОНТРОЛЬНЫЕ ВОПРОСЫ")
    questions = [
        ("1", "Что называется формальной системой?", "Формальная система — это совокупность алфавитов, аксиом и правил, задающих допустимые преобразования слов."),
        ("2", "Из чего состоит система Поста?", "Из внешнего алфавита A, множества переменных X, аксиом A₁ и множества продукций R."),
        ("3", "Что такое внешняя буква?", "Символ внешнего алфавита, который непосредственно входит в слова системы."),
        ("4", "Что обозначает переменная?", "Произвольное слово, подставляемое в левую и правую части продукции."),
        ("5", "Когда продукция применима?", "Когда её левая часть после некоторой подстановки полностью совпадает с текущим словом."),
        ("6", "Что такое аксиома?", "Исходное слово, с которого начинается вывод в формальной системе."),
        ("7", "Что такое вывод?", "Последовательность слов, полученных из аксиомы последовательным применением продукций."),
        ("8", "Когда вычисление останавливается?", "Когда применимых продукций больше нет или получена конечная конфигурация."),
        ("9", "Как представляются числа в работе?", "В унарной системе: число n представлено словом из n символов 1."),
        ("10", "Как вычисляется (x+1)(y+1)?", "Сначала к обоим множителям добавляется единица, затем второй множитель копируется по одному разу для каждой единицы первого."),
    ]
    add_table(doc, "Таблица 7 — Ответы на контрольные вопросы", ["№", "Вопрос", "Ответ"], questions, font_size=8.5)

    add_heading(doc, "ВЫВОД")
    add_body(doc, "В лабораторной работе для варианта 20 построена каноническая система Поста, вычисляющая функцию f(x, y) = (x + 1)(y + 1) в унарном представлении. Система содержит отдельные фазы увеличения аргументов, умножения и удаления служебных символов.")
    add_body(doc, "Разработан программный эмулятор, который считывает описание FSₚ из одного файла, контролирует принадлежность символов и переменных заданным множествам, выполняет правила и сохраняет пошаговый протокол. Для тестового слова 11/11= получен результат 111111111, что подтверждает корректность построения.")

    add_heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")
    for reference in [
        "1. Методические указания к лабораторной работе № 3 по дисциплине «Теория вычислительных процессов». — СПб.: ГУАП.",
        "2. Алферова З. В. Теория алгоритмов: учебное пособие для вузов. — М.: Статистика, 1973. — 164 с.",
        "3. Городецкий В. И. Прикладная алгебра и дискретная математика. Ч. 2. Формальные системы логического типа. — МО СССР, 1986. — 200 с.",
        "4. Городецкий В. И. Прикладная алгебра и дискретная математика. Ч. 3. Формальные системы логического типа. — МО СССР, 1987. — 177 с.",
        "5. Мальцев А. И. Алгоритмы и рекурсивные функции. — М.: Наука, 1986. — 368 с.",
        "6. Санкт-Петербургский государственный университет аэрокосмического приборостроения. Нормативная документация учебного процесса. — URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 15.10.2026).",
    ]:
        paragraph = doc.add_paragraph(style="Normal")
        paragraph.paragraph_format.first_line_indent = Cm(1.25)
        run = paragraph.add_run(reference)
        set_run_font(run, size=14)

    add_heading(doc, "Приложение А. Листинг программы-эмулятора")
    add_code(doc, source, size=7.0)
    doc.save(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    build()
