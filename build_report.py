from docx import Document
from docx.shared import Cm, Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path
import re
root=Path(__file__).resolve().parent/'lab4simulink'
out=root/'Отчет_ЛР4_вариант20.docx'
doc=Document(root/'official_lab_title.docx')
# Reuse and fill the official title form.
for i,text in [(3,'КАФЕДРА № 43'),(9,'')]:
 p=doc.paragraphs[i]; p.text=text
# Title text and discipline in the existing form.
doc.tables[1].cell(1,0).text='Моделирование непрерывных и дискретных систем'
doc.tables[1].cell(3,0).text='Компьютерное моделирование'
doc.tables[1].cell(4,0).text='Вариант 20'
# Teacher name in rightmost field above its label.
doc.tables[0].cell(0,4).text='Колесникова С.И.'
# Student group in group field; student name above its rightmost name label.
doc.tables[2].cell(0,1).text='4332'
doc.tables[2].cell(0,5).text='Могилатов С.И.'
# Title page formatting reset so body indents do not affect form.
for p in doc.paragraphs:
 p.paragraph_format.left_indent=Cm(0); p.paragraph_format.right_indent=Cm(0); p.paragraph_format.first_line_indent=Cm(0)
 for r in p.runs: r.font.name='Times New Roman'; r.font.size=Pt(14)
for table in doc.tables:
 for row in table.rows:
  for cell in row.cells:
   for p in cell.paragraphs:
    p.paragraph_format.left_indent=Cm(0); p.paragraph_format.right_indent=Cm(0); p.paragraph_format.first_line_indent=Cm(0)
    for r in p.runs: r.font.name='Times New Roman'; r.font.size=Pt(12)
# Remove inherited page-break runs from the blank title form so the cover stays one page.
for p in doc.paragraphs:
 for br in list(p._p.xpath('.//w:br[@w:type="page"]')): br.getparent().remove(br)
for table in doc.tables:
 for row in table.rows:
  for cell in row.cells:
   for p in cell.paragraphs:
    for br in list(p._p.xpath('.//w:br[@w:type="page"]')): br.getparent().remove(br)
# New body section.
sec=doc.add_section(WD_SECTION.CONTINUOUS)
sec.top_margin=Cm(2); sec.bottom_margin=Cm(2); sec.left_margin=Cm(3); sec.right_margin=Cm(1.5)
# Start contents on own page.
style=doc.styles['Normal']; style.font.name='Times New Roman'; style.font.size=Pt(14)
style._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
style.paragraph_format.line_spacing=1.5; style.paragraph_format.first_line_indent=Cm(1.25); style.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY

_first_heading=True
def page_heading(title):
 global _first_heading
 if not _first_heading: doc.add_page_break()
 _first_heading=False
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent=Cm(0); r=p.add_run(title.upper()); r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(14)
def heading(text,level=1):
 p=doc.add_paragraph(style=f'Heading {level}'); p.paragraph_format.first_line_indent=Cm(1.25); p.paragraph_format.keep_with_next=True; r=p.add_run(text); r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(14)
def para(text):
 p=doc.add_paragraph(text); p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY; return p
def equation(text):
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent=Cm(0); p.add_run(text)
def figure(name,caption,width=6.0):
 path=root/'figures'/name
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.keep_with_next=True
 p.add_run().add_picture(str(path),width=Inches(width))
 c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.first_line_indent=Cm(0); c.paragraph_format.line_spacing=1.0; c.paragraph_format.keep_with_next=True; c.add_run(caption)
# Contents: page numbers intentionally not fixed until final layout; document navigation uses headings.
page_heading('Содержание')
for line in ['ВВЕДЕНИЕ ........................................ 3','1 Нелинейное уравнение второго порядка ............ 4','2 Система дифференциальных уравнений .............. 7','3 Оценка погрешности дискретизации ................. 9','4 Ответы на контрольные вопросы .................. 10','ЗАКЛЮЧЕНИЕ ....................................... 11','СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ ................. 12','ПРИЛОЖЕНИЕ А Описание моделей и запуск ........... 13']:
 p=doc.add_paragraph(line); p.paragraph_format.first_line_indent=Cm(0)
page_heading('Введение')
para('В лабораторной работе исследуются непрерывные и дискретные модели, построенные для варианта 20 в MATLAB Simulink. Рассматриваются нелинейное дифференциальное уравнение второго порядка и линейная система двух уравнений. Для дискретизации применена прямая схема Ньютона (явный метод Эйлера). Сравнение с непрерывными решениями показывает влияние шага на точность, а параметры решателя — на точность численного интегрирования.')
heading('Цель работы')
para('Освоить моделирование непрерывных процессов в MATLAB Simulink, получить дискретные модели и оценить погрешность дискретизации.')
heading('Исходные данные')
para('Задание 1: y″y′ = 18y, y(5) = 1, y′(5) = 3. Задание 2: x′ = 2x + 4y, y′ = 4x + 2y, x(0) = 3, y(0) = 0. Методические указания не устанавливают интервалы моделирования, поэтому для первого уравнения выбран интервал [5; 7], для системы — [0; 1]. Для исследования дискретизации использованы шаги h = 0,1; 0,05; 0,01.')
page_heading('1 Нелинейное уравнение второго порядка')
heading('1.1 Непрерывная модель',2)
para('Введем v = y′. При v ≠ 0 исходное уравнение приводится к системе y′ = v, v′ = 18y/v, y(5) = 1, v(5) = 3. Непрерывная схема содержит интегратор y с начальным значением 1 и интегратор v с начальным значением 3. Сигнал y умножается на 18 и делится на v; полученное значение поступает на вход интегратора v. Выходы состояний сохраняются в рабочее пространство блоками To Workspace.')
figure('schema_1_0.png','Рисунок 1 — Непрерывная модель нелинейного уравнения')
para('Точное решение на выбранном интервале: y(t) = (t − 4)³, v(t) = 3(t − 4)². Подстановка подтверждает исходное уравнение и начальные условия. Начальная точка фазовой траектории (y, v) равна (1; 3), конечная при t = 7 — (27; 27).')
heading('1.2 Дискретная модель',2)
para('По прямой схеме Ньютона при tₖ = 5 + kh получаем:')
equation('yₖ₊₁ = yₖ + h vₖ;     vₖ₊₁ = vₖ + h · 18yₖ/vₖ;     y₀ = 1, v₀ = 3.')
para('Обе правые части вычисляются по состояниям предыдущего шага. Дискретная схема содержит два блока Discrete-Time Integrator с методом Forward Euler, усилитель и блок деления. Период дискретизации равен h.')
figure('schema_1_1.png','Рисунок 2 — Дискретная модель нелинейного уравнения')
figure('results_1.png','Рисунок 3 — Решение и фазовые портреты первого задания')
figure('states_1.png','Рисунок 4 — Сравнение обеих координат первого задания')
figure('comparison_1.png','Рисунок 5 — Влияние параметра и настроек решателя')
para('На рисунке 5 изменяется коэффициент a в уравнении y″y′ = ay: использованы a = 12, 18 и 24 при неизменных начальных условиях. Скорость роста решения зависит от коэффициента. На правой панели сравниваются решатели ode23 и ode45 при допусках 10⁻³, 10⁻⁶ и 10⁻⁹.')
page_heading('2 Система дифференциальных уравнений')
heading('2.1 Непрерывная модель',2)
para('Непрерывная схема имеет два интегратора с начальными значениями x(0) = 3 и y(0) = 0, четыре усилителя и два сумматора. Усилители с коэффициентами 2 и 4 формируют слагаемые производной x; коэффициенты 4 и 2 — слагаемые производной y. Сумматоры подают производные на соответствующие интеграторы. Состояния записываются блоками To Workspace.')
figure('schema_2_0.png','Рисунок 6 — Непрерывная модель системы')
para('Точное решение системы:')
equation('x(t) = 1,5(e⁶ᵗ + e⁻²ᵗ);     y(t) = 1,5(e⁶ᵗ − e⁻²ᵗ).')
para('Начальная точка фазовой траектории (x, y) = (3; 0), конечная при t = 1 — (605,34619; 604,94019).')
heading('2.2 Дискретная модель',2)
para('Прямая схема Ньютона дает:')
equation('xₖ₊₁ = xₖ + h(2xₖ + 4yₖ);     yₖ₊₁ = yₖ + h(4xₖ + 2yₖ);     x₀ = 3, y₀ = 0.')
para('В обоих уравнениях правые части используют значения предыдущего такта, то есть состояния обновляются одновременно. Два блока Discrete-Time Integrator настроены на Forward Euler и период h.')
figure('schema_2_1.png','Рисунок 7 — Дискретная модель системы')
figure('results_2.png','Рисунок 8 — Решение и фазовые портреты второго задания')
figure('states_2.png','Рисунок 9 — Сравнение обеих координат второго задания')
figure('comparison_2.png','Рисунок 10 — Влияние параметров и настроек решателя')
para('Для исследования параметра b рассматривалась система x′ = 2x + by, y′ = bx + 2y при b = 2, 4 и 6. При увеличении b растет скорость увеличения состояний. На правой панели сравниваются ode23 и ode45 при допусках 10⁻³, 10⁻⁶ и 10⁻⁹; ошибка вычисляется относительно точного решения.')
page_heading('3 Оценка погрешности дискретизации')
para('Погрешность в таблице определяется как максимум по узлам дискретной сетки модуля разности дискретного и точного решений каждой координаты. Для непрерывной модели использован ode45 с RelTol = 10⁻⁹ и AbsTol = 10⁻¹¹. Дискретная модель работает с постоянным шагом h.')
t=doc.add_table(rows=1,cols=4); t.alignment=1
for c,v in zip(t.rows[0].cells,['Задание','Шаг h','Максимальная ошибка координаты 1','Максимальная ошибка координаты 2']): c.text=v
rows=[('1','0,10','2,330145','1,407268'),('1','0,05','1,201898','0,720207'),('1','0,01','0,246495','0,146757'),('2','0,10','440,258388','440,174504'),('2','0,05','320,089372','320,048096'),('2','0,01','96,194139','96,185991')]
for row in rows:
 cells=t.add_row().cells
 for c,v in zip(cells,row): c.text=v
p=doc.add_paragraph('Таблица 1 — Максимальная ошибка дискретного решения на интервале моделирования'); p.paragraph_format.first_line_indent=Cm(0)
para('При уменьшении шага ошибка явного метода снижается. Во второй системе абсолютная погрешность велика из-за быстрого роста решения на интервале [0; 1]. Это показывает, что при выборе шага необходимо учитывать динамику системы, а визуальное сходство кривых само по себе не гарантирует малую ошибку.')
page_heading('4 Ответы на контрольные вопросы')
qs=[('1. Основные блоки Simulink для непрерывных систем','Integrator, Sum, Gain, Product и Divide, источники сигналов и средства наблюдения Scope, XY Graph или To Workspace.'),('2. Основные блоки для дискретных систем','Discrete-Time Integrator, Unit Delay, Zero-Order Hold, арифметические блоки и средства вывода. Период дискретизации задается параметром Sample time.'),('3. Задание начального значения, интеграла и графика','Начальное значение указывается в параметре Initial condition интегратора. Определенный интеграл находят по разности значений интегратора в начале и конце интервала. График строят блоками Scope или XY Graph либо экспортируют сигнал в MATLAB.'),('4. Типы дискретных интеграторов','Forward Euler использует значение входа на предыдущем такте; Backward Euler — на текущем; трапецеидальный метод усредняет значения входа на соседних тактах. Методы отличаются точностью и устойчивостью.'),('5. Всегда ли дискретное решение похоже на непрерывное?','Нет. При слишком большом шаге погрешность растет, а численная схема может иметь свойства устойчивости, отличные от непрерывной модели. Сходство зависит от уравнения, шага и настроек решателя.')]
for h,body in qs: heading(h,2); para(body)
page_heading('Заключение')
para('Для обоих заданий построены непрерывные модели и дискретные модели по прямой схеме Ньютона. Получены графики состояний и фазовые портреты, начальные и конечные точки указаны. Сравнение шагов показало уменьшение максимальной ошибки при уменьшении h. Влияние параметров уравнений и настроек численного решателя исследовано графически. Модели запускались в MATLAB R2023a Simulink, конечные значения сверены с точными решениями и рекуррентными формулами.')
page_heading('Список использованных источников')
para('1. Лабораторная работа 4. Моделирование непрерывных и дискретных систем, описываемых дифференциальными и разностными уравнениями в MatLab Simulink: методические указания. Вариант 20. С. 11.')
para('2. MathWorks. Simulink Documentation [Электронный ресурс]. URL: https://www.mathworks.com/help/simulink/ (дата обращения: 05.11.2026).')
para('3. ГУАП. Нормативная документация для учебного процесса [Электронный ресурс]. URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 05.11.2026).')
page_heading('Приложение А Описание моделей и запуск')
for name,description in [
('lr4_v20_task1_d0.slx','Непрерывное нелинейное уравнение. State1 формирует y из v; State2 формирует v из 18y/v. Начальные значения 1 и 3, интервал [5; 7].'),
('lr4_v20_task1_d1.slx','Дискретное нелинейное уравнение. Два интегратора Forward Euler реализуют рекуррентные формулы с шагом h.'),
('lr4_v20_task2_d0.slx','Непрерывная система. Два интегратора состояний x и y, четыре усилителя и два сумматора реализуют заданную линейную систему на [0; 1].'),
('lr4_v20_task2_d1.slx','Дискретная система. Дискретные интеграторы Forward Euler обновляют состояния с постоянным шагом h.')]:
 heading(name,2); para(description)
para('Для воспроизведения графиков и таблицы в MATLAB откройте папку с моделями и выполните run_experiments.m. Для проверки конечных значений выполните verify_models.m. Исходные данные варианта и начальные значения заданы в моделях и сценарии расчета.')
# Page numbering field in footer, hide on first page.
for section in doc.sections:
 section.footer_distance=Cm(1)
 footer=section.footer.paragraphs[0]
 for child in list(footer._p):
  if child.tag != qn('w:pPr'): footer._p.remove(child)
 footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
 fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)
 for p in section.first_page_footer.paragraphs:
  for child in list(p._p):
   if child.tag != qn('w:pPr'): p._p.remove(child)
# Title-page footer should not display number.
first=doc.sections[0]; first.different_first_page_header_footer=True
# body first-page is the contents page in second section; title page remains distinct.
doc.core_properties.title='Лабораторная работа 4 — вариант 20'
doc.core_properties.subject='Компьютерное моделирование'
doc.core_properties.author='Могилатов Семен Игоревич'
doc.save(out)
print(out)
