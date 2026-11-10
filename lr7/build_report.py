from __future__ import annotations

import json
import statistics
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TEMPLATE = ROOT / "title_template.docx"
SUMMARY = json.loads((RESULTS / "results_summary.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "report.docx"


def set_font(run, name="Times New Roman", size=14, bold=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def set_cell(cell, text, size=11, bold=None):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.right_indent = Cm(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    set_font(p.add_run(str(text)), size=size, bold=bold)


def page_field(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    r = paragraph.add_run()
    for tag, attrs in (("begin", {"w:fldCharType":"begin"}),):
        el=OxmlElement("w:fldChar")
        for k,v in attrs.items(): el.set(qn(k),v)
        r._r.append(el)
    instr=OxmlElement("w:instrText");instr.set(qn("xml:space"),"preserve");instr.text=" PAGE "
    r._r.append(instr)
    sep=OxmlElement("w:fldChar");sep.set(qn("w:fldCharType"),"separate");r._r.append(sep)
    value=OxmlElement("w:t");value.text="2";r._r.append(value)
    end=OxmlElement("w:fldChar");end.set(qn("w:fldCharType"),"end");r._r.append(end)
    set_font(r,size=12)


def toc_field(paragraph):
    paragraph.paragraph_format.first_line_indent=Cm(0)
    paragraph.paragraph_format.line_spacing=1.15
    r=paragraph.add_run()
    begin=OxmlElement("w:fldChar");begin.set(qn("w:fldCharType"),"begin");r._r.append(begin)
    instr=OxmlElement("w:instrText");instr.set(qn("xml:space"),"preserve");instr.text=' TOC \\o "1-2" \\h \\z \\u ';r._r.append(instr)
    sep=OxmlElement("w:fldChar");sep.set(qn("w:fldCharType"),"separate");r._r.append(sep)
    fallback=OxmlElement("w:t");fallback.text="Обновите поле содержания в Microsoft Word";r._r.append(fallback)
    end=OxmlElement("w:fldChar");end.set(qn("w:fldCharType"),"end");r._r.append(end)


def body(doc, text, *, size=14, first=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, keep=False):
    p=doc.add_paragraph(style="Normal")
    p.alignment=align
    p.paragraph_format.first_line_indent=Cm(1.25 if first else 0)
    p.paragraph_format.left_indent=Cm(0)
    p.paragraph_format.right_indent=Cm(0)
    p.paragraph_format.space_before=Pt(0)
    p.paragraph_format.space_after=Pt(0)
    p.paragraph_format.line_spacing=1.5
    p.paragraph_format.keep_together=keep
    set_font(p.add_run(text),size=size)
    return p


def heading(doc, text, level=1, *, centered=False, page_break=False):
    p=doc.add_paragraph(style=f"Heading {level}")
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent=Cm(0 if centered else 1.25)
    p.paragraph_format.left_indent=Cm(0);p.paragraph_format.right_indent=Cm(0)
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(7 if level==1 else 4)
    p.paragraph_format.line_spacing=1.5;p.paragraph_format.keep_with_next=True
    p.paragraph_format.page_break_before=page_break
    set_font(p.add_run(text),size=14,bold=True)
    return p


def table(doc, title, headers, rows, widths, size=9.5):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Pt(4)
    p.paragraph_format.space_after=Pt(3);p.paragraph_format.keep_with_next=True
    set_font(p.add_run(title),size=12)
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    borders=OxmlElement("w:tblBorders")
    for edge in ("top","left","bottom","right","insideH","insideV"):
        el=OxmlElement(f"w:{edge}");el.set(qn("w:val"),"single");el.set(qn("w:sz"),"4");el.set(qn("w:color"),"777777");borders.append(el)
    t._tbl.tblPr.append(borders)
    for i,label in enumerate(headers):
        set_cell(t.rows[0].cells[i],label,size=size,bold=True)
        shd=OxmlElement("w:shd");shd.set(qn("w:fill"),"D9E2F3");t.rows[0].cells[i]._tc.get_or_add_tcPr().append(shd)
    repeat=OxmlElement("w:tblHeader");repeat.set(qn("w:val"),"true");t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        cells=t.add_row().cells
        for i,value in enumerate(row):
            set_cell(cells[i],value,size=size)
    for row in t.rows:
        for i,width in enumerate(widths): row.cells[i].width=Cm(width)
    spacer=doc.add_paragraph();spacer.paragraph_format.space_after=Pt(0);spacer.paragraph_format.space_before=Pt(0);spacer.paragraph_format.line_spacing=Pt(1)
    return t


def figure(doc,path,caption,width=15.5):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(2);p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(path),width=Cm(width))
    c=doc.add_paragraph();c.alignment=WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.first_line_indent=Cm(0);c.paragraph_format.space_after=Pt(6);c.paragraph_format.keep_together=True
    set_font(c.add_run(caption),size=12)


def code_appendix(doc, letter, label, filename):
    heading(doc,f"ПРИЛОЖЕНИЕ {letter}",1,centered=True,page_break=True)
    heading(doc,label,2,centered=True)
    for line in (ROOT/filename).read_text(encoding="utf-8").splitlines():
        p=doc.add_paragraph();p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.left_indent=Cm(0);p.paragraph_format.right_indent=Cm(0)
        p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.0
        set_font(p.add_run(line or " "),name="Consolas",size=7.0)


def fmt(v, sig=3):
    return f"{v:.{sig}g}"


def main():
    doc=Document(TEMPLATE)
    section=doc.sections[0]
    section.top_margin=Cm(2);section.bottom_margin=Cm(2);section.left_margin=Cm(3);section.right_margin=Cm(1.5)
    section.different_first_page_header_footer=True
    section.footer.is_linked_to_previous=False
    page_field(section.footer.paragraphs[0]);section.first_page_footer.paragraphs[0].clear()
    normal=doc.styles["Normal"];normal.font.name="Times New Roman";normal.font.size=Pt(14)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"),"Times New Roman")
    normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;normal.paragraph_format.first_line_indent=Cm(1.25)
    normal.paragraph_format.line_spacing=1.5;normal.paragraph_format.space_after=Pt(0)

    # Fill values into the corresponding fields of the official GUAP lab title form.
    doc.paragraphs[1].text="КАФЕДРА № 43"
    doc.paragraphs[1].alignment=WD_ALIGN_PARAGRAPH.CENTER
    set_cell(doc.tables[0].rows[0].cells[-1],"Скобцов Ю.А.",size=12)
    title=doc.tables[1]
    set_cell(title.rows[0].cells[0],"ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 7",size=14,bold=True)
    set_cell(title.rows[1].cells[0],"Оптимизация функций многих переменных с помощью роевых алгоритмов\nВариант 4",size=12)
    set_cell(title.rows[2].cells[0],"по курсу: Эволюционные методы проектирования программно-информационных систем",size=12)
    set_cell(doc.tables[2].rows[0].cells[1],"4332",size=12)
    set_cell(doc.tables[2].rows[0].cells[-1],"Могилатов С.И.",size=12)
    doc.paragraphs[-1].text="Санкт-Петербург 2026";doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Cm(0)
    set_font(p.add_run("СОДЕРЖАНИЕ"),size=14,bold=True)
    toc=doc.add_paragraph();toc_field(toc)

    heading(doc,"ВВЕДЕНИЕ",1,centered=True)
    body(doc,"Роевой алгоритм частиц (PSO) ищет экстремум непрерывной функции, перемещая набор точек-пробных решений. Скорость каждой частицы зависит от её прежнего движения, лучшей собственной позиции и лучшей найденной роем позиции. В лабораторной работе этот метод применяется к сдвинутой осепараллельной гиперэллипсоидной функции варианта 4.")
    body(doc,"Цель работы — реализовать глобальный PSO, показать поверхность двумерной функции и движение частиц по поколениям, исследовать влияние размерности, числа частиц, коэффициента инерции и критерия остановки.")
    body(doc,"Отчёт содержит постановку задачи, описание алгоритма, воспроизводимые параметры и исходный код, результаты пяти повторов для n=2, 3, 5 и 10, графики и ответы на контрольные вопросы. Правила оформления проверены по актуальным требованиям ГУАП [1].")

    heading(doc,"1 ЗАДАНИЕ И ПОСТАНОВКА ЗАДАЧИ",1,page_break=True)
    heading(doc,"1.1 Индивидуальное задание",2)
    body(doc,"Вариант 4 — Moved axis parallel hyper-ellipsoid function. В таблице указаны глобальный минимум f(x)=0 и координаты x_i=5i для i=1,…,n. Практическая часть требует построить график функции и показать популяцию при n=2, предусмотреть пошаговый просмотр, исследовать влияние размера популяции и критерия останова, а также сравнить поиск для n=3, 5 и 10 [2].")
    body(doc,"В методичке напечатана формула Σ5i·x_i², которая минимальна в нуле, хотя рядом заявлена точка x_i=5i и функция названа сдвинутой. Чтобы согласовать название и объявленный минимум, в расчётах используется f_n(x)=Σ_{i=1}^n 5i(x_i−5i)². При таком определении f_n(x*)=0 в x*=(5,10,…,5n). Этот выбор трактовки явно фиксируется, поскольку исходная строка задания противоречива.")
    body(doc,"Методичка не указывает границы поиска для этой строки. В программе принят общий диапазон x_i∈[−55,55] для всех координат: он включает целевые значения до 50 при n=10 и оставляет оптимум внутри области. Это экспериментальное допущение, а не ограничение из таблицы задания.")
    heading(doc,"1.2 Математическая модель",2)
    body(doc,"Для каждого числа измерений n целевая функция задаётся суммой независимых квадратичных слагаемых с положительными весами: f_n(x)=Σ_{i=1}^n 5i(x_i−5i)². Производная по координате равна ∂f/∂x_i=10·5i(x_i−5i); поэтому единственная стационарная точка — x_i=5i. Все веса положительны, матрица Гессе диагональна и положительно определена, следовательно эта точка является единственным глобальным минимумом с f*=0.")
    body(doc,"Для двумерного случая f_2(x_1,x_2)=5(x_1−5)²+10(x_2−10)². Линии уровня — эллипсы с центром в (5,10).")

    heading(doc,"2 ТЕОРЕТИЧЕСКИЕ СВЕДЕНИЯ",1,page_break=True)
    heading(doc,"2.1 Глобальный роевой алгоритм",2)
    body(doc,"В PSO каждая частица i имеет положение x_i(t), скорость v_i(t), личный лучший результат p_i и вектор глобально лучшей позиции g. После оценки функции память частицы обновляется, если новое положение лучше прежнего. Затем скорость и позиция рассчитываются по формулам [2; 3]:")
    body(doc,"v_i(t+1)=w·v_i(t)+c_1·r_1·(p_i−x_i(t))+c_2·r_2·(g−x_i(t));  x_i(t+1)=x_i(t)+v_i(t+1).",first=False,align=WD_ALIGN_PARAGRAPH.CENTER)
    body(doc,"Здесь w — инерционный вес; c₁ и c₂ — когнитивный и социальный коэффициенты; r₁ и r₂ — независимые случайные числа из [0,1]. Когнитивная часть направляет частицу к её собственному историческому успеху, социальная — к лучшему решению роя. Обмен информацией со всеми частицами образует глобальную структуру соседства.")
    body(doc,"Исходная формула методички не содержит множитель инерции, то есть соответствует w=1, и рекомендует c₁=c₂=2. В программе применяется инерционная модификация PSO с w=0,7298 и c₁=c₂=1,49618 [4]. Это делает явным контроль переноса скорости; вес w отдельно исследуется. Для случайных множителей используются равномерные значения [0,1], как в канонической записи PSO. Фраза методички о нормальном распределении при одновременно указанном интервале [0,1] неоднозначна.")
    heading(doc,"2.2 Границы и критерий останова",2)
    body(doc,"Скорость ограничивается по модулю 20% ширины области, чтобы отдельный шаг не переносил частицу через весь диапазон. При выходе за границу применяется отражение и частичное гашение скорости. Остановка базового запуска наступает при f_best≤10⁻⁸, при отсутствии улучшения 100 поколений либо после 1000 поколений. При исследовании patience порог f отключается, чтобы изолировать действие стагнационного критерия.")
    heading(doc,"3 ПРОГРАММНАЯ РЕАЛИЗАЦИЯ И ПЛАН ЭКСПЕРИМЕНТА",1,page_break=True)
    heading(doc,"3.1 Последовательность работы программы",2)
    for text in [
        "1. Создать воспроизводимый генератор случайных чисел по заданному seed и равномерно инициализировать положения и скорости частиц.",
        "2. Вычислить f(x) для всех частиц; сохранить их личные лучшие позиции и выбрать глобально лучшую.",
        "3. На каждом поколении вычислить новую скорость с инерционной, когнитивной и социальной составляющими.",
        "4. Ограничить скорость, отразить координаты у границ, пересчитать функцию и обновить личный и глобальный рекорды.",
        "5. Записать лучшее и среднее значение функции; проверить точность, стагнацию и возраст популяции.",
        "6. Сохранить CSV/JSON, график поверхности с популяцией, снимки поиска, кривые сходимости и диаграммы параметров.",
    ]:
        p=body(doc,text,first=False,size=12.5);p.paragraph_format.left_indent=Cm(0.55);p.paragraph_format.hanging_indent=Cm(0.45);p.paragraph_format.line_spacing=1.2
    body(doc,"Модуль алгоритма находится в приложении А, сценарий запусков и построения графиков — в приложении Б. Программа поддерживает краткую сводку и режим --verbose с печатью истории демонстрационного запуска.")
    heading(doc,"3.2 Настройки серий",2)
    body(doc,"Демонстрационный запуск: n=2, 60 частиц, w=0,7298, c₁=c₂=1,49618, seed=247, точность 10⁻⁸ и patience=100. Сравнения размерностей и параметров повторяются на пяти seed; за раз меняется один фактор.")
    table(doc,"Таблица 2 — Настройки экспериментов",["Серия","Параметр","Значения","Повторов"],[
        ("Размерность","n","2, 3, 5, 10","5 на n"),("Размер роя","число частиц","20, 40, 80, 120","5 на значение"),
        ("Инерция","w","0,4; 0,7298; 0,9","5 на значение"),("Остановка","patience","30, 60, 120; f-порог отключён","5 на значение"),
        ("Общие","c₁=c₂; диапазон","1,49618; [−55,55]","фиксированы"),
    ],[3.0,3.0,7.8,2.0],size=9.5)
    body(doc,"Мутация к PSO неприменима: алгоритм не использует генетических операторов. Вместо её вероятности исследуется инерционный вес w, напрямую влияющий на движение частиц.")

    heading(doc,"4 РЕЗУЛЬТАТЫ",1,page_break=True)
    demo=SUMMARY["demo"]
    body(doc,f"Для n=2 при seed=247 найдено x=({demo['best_position'][0]:.8f}; {demo['best_position'][1]:.8f}) и f={demo['best_value']:.3g}. Точное решение — (5; 10), f*=0; евклидова ошибка координат равна {demo['position_error']:.3g}. Порог f≤10⁻⁸ достигнут за {demo['generations']} поколений; вычислительное время составило {demo['elapsed_seconds']:.4f} с.")
    body(doc,"Рисунок 1 показывает поверхность двумерной целевой функции и положение частиц последнего поколения. Для точного чтения области поиска линии уровня и числовые оси дополнены на рисунке 2; снимки поколений показывают стягивание роя к центру эллиптической впадины.")
    figure(doc,RESULTS/"surface_population.png","Рисунок 1 — Поверхность функции и частицы последнего поколения",14.2)
    figure(doc,RESULTS/"function_population.png","Рисунок 2 — Линии уровня функции и найденный минимум",14.2)
    figure(doc,RESULTS/"search_steps.png","Рисунок 3 — Пошаговое сближение частиц с минимумом",15.0)
    figure(doc,RESULTS/"convergence_dimensions.png","Рисунок 4 — Сходимость для n=2, 3, 5 и 10",14.7)

    heading(doc,"4.1 Влияние размерности",2)
    dim_rows=[]
    for n in (2,3,5,10):
        stats=SUMMARY["dimension_summary"]
        dim_rows.append((str(n),f"{stats['mean_best'][str(n)]['mean']:.2e}",f"{stats['mean_position_error'][str(n)]['mean']:.2e}",
            f"{stats['mean_generations'][str(n)]['mean']:.1f}",f"{stats['mean_seconds'][str(n)]['mean']:.4f}"))
    body(doc,"Сводные средние значения и ошибки координат для четырёх размерностей приведены в таблице 3.")
    table(doc,"Таблица 3 — Средние результаты по пяти запускам",["n","Среднее f best","Ошибка координат","Поколения","Время, с"],dim_rows,[1.2,3.5,3.7,3.0,2.5],size=9.5)
    body(doc,"Во всех двадцати измерениях алгоритм достиг порога 10⁻⁸. При росте числа координат средние поколения и время увеличились: у более размерной задачи выше число степеней свободы и сложнее одновременно сократить ошибку каждой координаты. Времена отражают локальные короткие запуски и зависят от состояния компьютера; сравнение поколений устойчивее сравнения десятых долей миллисекунды.")

    heading(doc,"4.2 Влияние размера роя",2)
    pop_rows=[]
    for r in SUMMARY["population_study"]:
        pop_rows.append((str(r["particles"]),f"{r['mean_best']:.2e} ± {r['sd_best']:.1e}",f"{r['mean_generations']:.1f}",f"{r['mean_seconds']:.4f}",f"{r['successes']}/{r['runs']}"))
    body(doc,"Сравнение четырёх размеров роя по пяти независимым запускам сведено в таблицу 4.")
    table(doc,"Таблица 4 — Размер роя, пять повторов",["Частиц","Среднее f best ± SD","Поколения","Время, с","Порог достигнут"],pop_rows,[2.0,4.1,2.5,2.2,2.7],size=9)
    body(doc,"Зависимость среднего лучшего значения от размера роя показана на рисунке 5.")
    figure(doc,RESULTS/"population_accuracy.png","Рисунок 5 — Среднее лучшее значение при разном размере роя, логарифмическая шкала",14.5)
    body(doc,"Порог точности достигнут во всех сериях. Увеличение числа частиц сократило среднее число поколений примерно с 90 до 73, но увеличило время одного поиска с примерно 0,004 до 0,018 с. Лучшее среднее f не уменьшается монотонно с числом частиц, что ожидаемо для конечной выборки случайных запусков; по пяти повторам нельзя заключить, что конкретный размер всегда точнее.")

    heading(doc,"4.3 Влияние инерции",2)
    inertia_rows=[]
    for r in SUMMARY["inertia_study"]:
        inertia_rows.append((f"{r['inertia']:.4g}",f"{r['mean_best']:.2e} ± {r['sd_best']:.1e}",f"{r['mean_generations']:.1f}",f"{r['mean_seconds']:.4f}",f"{r['successes']}/{r['runs']}"))
    body(doc,"Сводка результатов для трёх значений инерции представлена в таблице 5.")
    table(doc,"Таблица 5 — Коэффициент инерции, пять повторов",["w","Среднее f best ± SD","Поколения","Время, с","Порог достигнут"],inertia_rows,[1.6,4.1,2.5,2.2,2.7],size=9)
    body(doc,"График среднего лучшего значения при изменении w приведён на рисунке 6.")
    figure(doc,RESULTS/"inertia_accuracy.png","Рисунок 6 — Среднее лучшее значение при разных w, логарифмическая шкала",14.5)
    body(doc,"В испытанных сериях w=0,4 и w=0,7298 достигли точности во всех пяти повторах. При w=0,9 порог достигнут только в одном повторе, а среднее лучшее значение заметно выше. На этой задаче чрезмерная инерция сохраняет большой шаг и затрудняет точное оседание роя у минимума. Это наблюдение относится к выбранным коэффициентам и диапазону, а не является универсальным правилом для всех PSO-задач.")

    heading(doc,"4.4 Критерий остановки",2)
    stop_rows=[]
    for r in SUMMARY["stopping_study"]:
        stop_rows.append((str(r["patience"]),f"{r['mean_best']:.2e} ± {r['sd_best']:.1e}",f"{r['mean_generations']:.1f}",f"{r['mean_seconds']:.4f}"))
    body(doc,"Сравнение трёх интервалов стагнации приведено в таблице 6.")
    table(doc,"Таблица 6 — Интервал стагнации без порога f",["Поколений без улучшения","Среднее f best ± SD","Поколения","Время, с"],stop_rows,[3.2,4.1,2.7,2.2],size=9)
    body(doc,"Зависимость числа поколений до останова от patience показана на рисунке 7.")
    figure(doc,RESULTS/"stopping_generations.png","Рисунок 7 — Среднее число поколений до остановки",14.5)
    body(doc,"При отключённом пороге по целевой функции больший patience позволил продолжить поиск: среднее число поколений выросло с 160 при patience=30 до 271 при patience=120. Среднее лучшее f стало меньше, однако расчёт также занял больше времени. Это показывает компромисс между ранней остановкой и дополнительным доуточнением решения. Пять повторов дают иллюстративную, а не статистически исчерпывающую оценку.")

    heading(doc,"5 ОТВЕТЫ НА КОНТРОЛЬНЫЕ ВОПРОСЫ",1,page_break=True)
    answers=[
        "Потенциальное решение представляется вектором вещественных координат частицы x_i=(x_i1,…,x_in).",
        "Координаты обновляются прибавлением новой скорости: x_i(t+1)=x_i(t)+v_i(t+1). Скорость включает прежнюю скорость, притяжение к личному лучшему и к глобально лучшему вектору.",
        "Когнитивная составляющая c₁r₁(p_i−x_i) возвращает частицу в сторону её собственной лучшей ранее найденной позиции.",
        "Социальная составляющая c₂r₂(g−x_i) направляет частицу к лучшему решению, найденному всем роем или её соседями.",
        "Глобальный PSO инициализирует позиции и скорости, оценивает целевую функцию, обновляет личный и глобальный рекорды, перемещает частицы и повторяет цикл до критерия останова.",
        "В глобальном PSO каждая частица использует лучшее решение всего роя; в локальном — лучшее решение ограниченного соседства. Локальный вариант распространяет информацию медленнее и может поддерживать разнообразие.",
        "Социальная структура задаёт, от каких соседей частица получает информацию. Примеры — глобальная звезда, кольцо, решётка и иные графы соседства.",
        "Локальный PSO задаёт окрестность каждой частицы, выбирает лучшего соседа и использует его позицию в социальной части формулы скорости вместо единого глобального рекорда.",
        "Личная лучшая позиция p_i — положение, в котором частица i достигла наименьшего значения функции среди всех её предыдущих посещений.",
        "Глобальная лучшая позиция g — лучшая из личных лучших позиций всех частиц роя на текущем шаге.",
        "К основным аспектам относятся кодирование решения координатами, инициализация роя, оценка качества, память p_i и g, обновление скорости и положения, обработка границ и критерий остановки.",
        "Обычно используют максимальное число поколений, достижение целевой точности, ограничение времени или отсутствие улучшения в течение заданного числа поколений.",
        "Положения обычно случайно и независимо выбираются внутри области поиска; начальные скорости задаются случайно в допустимом диапазоне. Для воспроизводимости фиксируют seed.",
        "Основные параметры: размер роя, инерционный вес w, когнитивный c₁ и социальный c₂ коэффициенты, диапазон скоростей, границы переменных и критерий остановки.",
        "Известны глобальные и локальные схемы, PSO с инерционным весом или коэффициентом сжатия, адаптивные и самоорганизующиеся варианты, а также дискретные и гибридные алгоритмы.",
        "PSO, эволюционные стратегии (ЭС) и генетические алгоритмы (ГА) — популяционные стохастические методы оптимизации. Они итеративно оценивают множество кандидатов и используют их качество для формирования следующих решений.",
        "PSO перемещает векторы решений с помощью скоростей и социальной памяти. ЭС изменяют непрерывные параметры мутацией и отбором родителей/потомков. ГА кодирует хромосомы и применяет отбор, кроссовер и мутацию. В базовом PSO генетических операторов нет.",
    ]
    for i,answer in enumerate(answers,1):
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.left_indent=Cm(.45);p.paragraph_format.line_spacing=1.5;p.paragraph_format.space_after=Pt(1)
        p.paragraph_format.page_break_before=(i==9)
        set_font(p.add_run(f"{i}. "),size=12,bold=True);set_font(p.add_run(answer),size=12)

    heading(doc,"ЗАКЛЮЧЕНИЕ",1,centered=True,page_break=True)
    body(doc,"Реализован глобальный роевой алгоритм для оптимизации функции варианта 4. В соответствии с объявленным в методичке минимумом исследовалась сдвинутая функция f_n(x)=Σ5i(x_i−5i)². Для n=2 найдено решение с f=1,64·10⁻⁹ и координатной ошибкой порядка 10⁻⁵; порог 10⁻⁸ достигнут за 63 поколения.")
    body(doc,"Во всех пяти повторах для каждой размерности n=2, 3, 5, 10 достигнут заданный порог. С увеличением размерности возросли средние поколения и время. Более крупный рой выполнял меньше поколений, но увеличивал время из-за большего числа вычислений на поколение. Инерция w=0,9 оказалась неудачной для выбранной задачи, а увеличение patience при отключённом целевом пороге давало более точные решения ценой дополнительного времени.")
    body(doc,"В исходной таблице задания есть противоречие между формулой и заявленной точкой минимума; кроме того, методичка просит исследовать вероятность мутации, которая относится к генетическому алгоритму, а не PSO. В отчёте приняты явные, проверяемые трактовки и представлены код, исходные данные запусков, графики и шаги поиска.")

    heading(doc,"СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",1,centered=True,page_break=True)
    sources=[
        "ГУАП. Для учебного процесса: нормативные требования к оформлению студенческих работ и бланки титульных листов лабораторных работ. URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 10.11.2026).",
        "Методические указания. Лабораторная работа № 7 «Оптимизация функций многих переменных с помощью роевых алгоритмов». Разделы 7.1–7.2 и приложение 1. Предоставленный учебный материал.",
        "Kennedy J., Eberhart R. Particle swarm optimization // Proceedings of ICNN’95 — International Conference on Neural Networks. 1995. Vol. 4. P. 1942–1948. DOI: 10.1109/ICNN.1995.488968.",
        "Shi Y., Eberhart R. A modified particle swarm optimizer // Proceedings of the IEEE International Conference on Evolutionary Computation. Anchorage, 1998. P. 69–73. DOI: 10.1109/ICEC.1998.699146.",
    ]
    for i,s in enumerate(sources,1):
        p=body(doc,f"{i}. {s}",first=True,size=12)

    code_appendix(doc,"А","Модуль глобального роевого алгоритма","pso.py")
    code_appendix(doc,"Б","Сценарий экспериментов и построения графиков","run_experiments.py")
    for p in doc.paragraphs[:8]:
        p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.left_indent=Cm(0);p.paragraph_format.right_indent=Cm(0)
    doc.core_properties.title="Лабораторная работа № 7 — Оптимизация функции методом PSO"
    doc.core_properties.subject="Эволюционные методы проектирования программно-информационных систем"
    doc.core_properties.author="Могилатов Семен Игоревич"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
