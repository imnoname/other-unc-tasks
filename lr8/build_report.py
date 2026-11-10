from __future__ import annotations
import csv, json
from pathlib import Path
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/'results'
SUMMARY=json.loads((RESULTS/'summary.json').read_text(encoding='utf-8'))

def font(run,size=14,bold=None,name='Times New Roman'):
    run.font.name=name
    rp=run._element.get_or_add_rPr(); rf=rp.rFonts
    rf.set(qn('w:ascii'),name); rf.set(qn('w:hAnsi'),name); rf.set(qn('w:eastAsia'),name)
    run.font.size=Pt(size)
    if bold is not None: run.bold=bold

def cell_text(cell,text,size=10,bold=None):
    cell.text=''; cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    p=cell.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.left_indent=Cm(0); p.paragraph_format.right_indent=Cm(0)
    p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
    font(p.add_run(str(text)),size,bold)

def body(doc,text,size=14,first=True,align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p=doc.add_paragraph(style='Normal'); p.alignment=align
    p.paragraph_format.first_line_indent=Cm(1.25 if first else 0); p.paragraph_format.left_indent=Cm(0);p.paragraph_format.right_indent=Cm(0)
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.5
    font(p.add_run(text),size);return p

def heading(doc,text,level=1,center=False,page=False):
    p=doc.add_paragraph(style=f'Heading {level}')
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent=Cm(0 if center else 1.25);p.paragraph_format.left_indent=Cm(0);p.paragraph_format.right_indent=Cm(0)
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(6 if level==1 else 4);p.paragraph_format.line_spacing=1.5
    p.paragraph_format.keep_with_next=True;p.paragraph_format.page_break_before=page
    font(p.add_run(text),14,True);return p

def table(doc,title,headers,rows,widths=None,size=9):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(3);p.paragraph_format.keep_with_next=True
    font(p.add_run(title),12)
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    pr=t._tbl.tblPr; borders=OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        e=OxmlElement(f'w:{edge}');e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'777777');borders.append(e)
    pr.append(borders)
    for i,h in enumerate(headers):
        cell_text(t.rows[0].cells[i],h,size,True);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'D9E2F3');t.rows[0].cells[i]._tc.get_or_add_tcPr().append(sh)
    rep=OxmlElement('w:tblHeader');rep.set(qn('w:val'),'true');t.rows[0]._tr.get_or_add_trPr().append(rep)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):cell_text(cells[i],v,size)
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths):row.cells[i].width=Cm(w)
    p=doc.add_paragraph();p.paragraph_format.line_spacing=Pt(1);p.paragraph_format.space_after=Pt(0)
    return t

def figure(doc,path,caption,width=15.5):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(2);p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(path),width=Cm(width))
    c=doc.add_paragraph();c.alignment=WD_ALIGN_PARAGRAPH.CENTER;c.paragraph_format.first_line_indent=Cm(0);c.paragraph_format.space_after=Pt(6);c.paragraph_format.keep_together=True;font(c.add_run(caption),12)

def page_field(p):
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Cm(0)
    r=p.add_run();begin=OxmlElement('w:fldChar');begin.set(qn('w:fldCharType'),'begin');r._r.append(begin)
    ins=OxmlElement('w:instrText');ins.set(qn('xml:space'),'preserve');ins.text=' PAGE ';r._r.append(ins)
    sep=OxmlElement('w:fldChar');sep.set(qn('w:fldCharType'),'separate');r._r.append(sep)
    val=OxmlElement('w:t');val.text='2';r._r.append(val)
    end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end');r._r.append(end);font(r,12)

def toc_field(p):
    p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.line_spacing=1.15
    r=p.add_run();b=OxmlElement('w:fldChar');b.set(qn('w:fldCharType'),'begin');r._r.append(b)
    ins=OxmlElement('w:instrText');ins.set(qn('xml:space'),'preserve');ins.text=' TOC \\o "1-2" \\h \\z \\u ';r._r.append(ins)
    s=OxmlElement('w:fldChar');s.set(qn('w:fldCharType'),'separate');r._r.append(s)
    txt=OxmlElement('w:t');txt.text='Содержание обновляется в Microsoft Word';r._r.append(txt)
    e=OxmlElement('w:fldChar');e.set(qn('w:fldCharType'),'end');r._r.append(e)

def code_listing(doc,title,filename):
    heading(doc,title,1,True,True)
    for line in (ROOT/filename).read_text(encoding='utf-8').splitlines():
        p=doc.add_paragraph();p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.left_indent=Cm(0);p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.0
        font(p.add_run(line or ' '),7,name='Consolas')

def main():
    doc=Document(ROOT/'title_template.docx')
    sec=doc.sections[0];sec.top_margin=Cm(2);sec.bottom_margin=Cm(2);sec.left_margin=Cm(3);sec.right_margin=Cm(1.5);sec.different_first_page_header_footer=True
    sec.footer.is_linked_to_previous=False;page_field(sec.footer.paragraphs[0]);sec.first_page_footer.paragraphs[0].clear()
    normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(14);normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman');normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;normal.paragraph_format.first_line_indent=Cm(1.25);normal.paragraph_format.line_spacing=1.5;normal.paragraph_format.space_after=Pt(0)
    doc.paragraphs[1].text='КАФЕДРА № 43';doc.paragraphs[1].alignment=WD_ALIGN_PARAGRAPH.CENTER
    cell_text(doc.tables[0].rows[0].cells[-1],'Скобцов Ю.А.',12)
    title=doc.tables[1]
    cell_text(title.rows[0].cells[0],'ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 8',14,True)
    cell_text(title.rows[1].cells[0],'Эволюционные алгоритмы оценки стоимости проектов в программной инженерии\nВариант 4',12)
    cell_text(title.rows[2].cells[0],'по курсу: Эволюционные методы проектирования программно-информационных систем',12)
    cell_text(doc.tables[2].rows[0].cells[1],'4332',12);cell_text(doc.tables[2].rows[0].cells[-1],'Могилатов С.И.',12)
    doc.paragraphs[-1].text='Санкт-Петербург 2026';doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break();p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Cm(0);font(p.add_run('СОДЕРЖАНИЕ'),14,True);toc_field(doc.add_paragraph());doc.add_page_break()
    heading(doc,'ВВЕДЕНИЕ',1,True)
    body(doc,'Оценка трудоёмкости проекта на ранней стадии разработки помогает планировать ресурсы и сроки, когда фактические затраты ещё неизвестны. Модель COCOMO связывает размер программного продукта с трудоёмкостью степенной зависимостью E_f=aL^b. Коэффициенты a и b определяют масштаб и скорость роста оценки; их можно настраивать по историческим данным проектов.')
    body(doc,'Цель лабораторной работы — реализовать генетический алгоритм для поиска коэффициентов модели COCOMO и проверить найденную формулу на отложенных данных. В варианте 4 используются вещественное кодирование, метрика ED, арифметические операторы скрещивания и мутации, а также рулеточный отбор [1]. Отчёт оформлен на титульном бланке ГУАП; параметры текста и структуры сверены с официальными правилами университета [2].')
    heading(doc,'1 ПОСТАНОВКА ЗАДАЧИ',1,page=True)
    heading(doc,'1.1 Исходные данные и вариант',2)
    body(doc,'Использованы 18 проектов из таблицы 8.1 методических указаний [1]. Размер L задан в тысячах строк кода, E_f — в человеко-месяцах. По заданию 13 проектов случайно отбираются для обучения, 5 — для теста; seed=3 фиксирует разбиение.')
    body(doc,'В проекте №4 напечатано E_f=909,8 человеко-месяца — значение резко выше остальных близких по размеру проектов. Оно сохранено как в источнике и попало в тест; метрики приведены с этой строкой и без неё.')
    rows=list(csv.DictReader((ROOT/'data/projects_18.csv').open(encoding='utf-8-sig')))
    body(doc,'Исходные данные и разбиение на выборки приведены в таблице 1.')
    table(doc,'Таблица 1 — Данные проектов HACA',["№","L, тыс. строк","E_f, чел.-мес."],[(r['project_id'],r['kloc'],r['effort_person_months']) for r in rows],[2,5,5],9)
    heading(doc,'1.2 Математическая постановка',2)
    body(doc,'Найти положительные a,b модели E_f(L)=aL^b, минимизируя среднеквадратичное евклидово расстояние (ED) на обучающих данных:')
    body(doc,'ED(a,b)=sqrt((1/N) * Σ[i=1..N](E_f,i − a * L_i^b)^2).',first=False,align=WD_ALIGN_PARAGRAPH.CENTER)
    body(doc,'В методических указаниях для параметров не дан численный диапазон. В программе установлены a∈[0,05; 20] и b∈[0,1; 2,5]. Границы обеспечивают положительные коэффициенты и содержат полученные значения; диапазоны являются настройкой эксперимента.')
    heading(doc,'2 ТЕОРЕТИЧЕСКИЕ СВЕДЕНИЯ',1,page=True)
    heading(doc,'2.1 Модель COCOMO',2)
    body(doc,'COCOMO (Constructive Cost Model) — параметрическая модель оценки затрат на создание программного обеспечения [3]. В базовой форме трудоёмкость выражается как E_f=aL^b, где L — размер кода, а a и b — параметры, определяемые по историческим данным. Поскольку показатели зависят от набора проектов и единиц измерения, их следует калибровать на репрезентативных наблюдениях.')
    body(doc,'Если взять натуральные логарифмы обеих частей, получаем ln(E_f)=ln(a)+b ln(L). Поэтому для сравнения в работе рассчитывается обычная лог-линейная регрессия. Она минимизирует квадратичную ошибку в логарифмическом пространстве и служит базовым ориентиром, тогда как генетический алгоритм напрямую минимизирует выбранную в варианте метрику ED в исходных единицах.')
    heading(doc,'2.2 Генетический алгоритм с вещественным кодированием',2)
    body(doc,'Генетические алгоритмы строят популяцию решений и постепенно улучшают её с помощью отбора и вариации кандидатов [4]. В этой работе хромосома — пара вещественных чисел (a,b). Каждое решение оценивается по ED на обучающем множестве. Так как требуется минимизировать ошибку, для рулеточного отбора ошибки преобразуются в положительные веса: вес кандидата равен max(ошибка популяции) − ошибка кандидата плюс малое положительное число. Чем ниже ED, тем больше вероятность стать родителем.')
    body(doc,'Арифметическое скрещивание двух родителей p и q образует потомка c=αp+(1−α)q, где α равномерно выбирается из [0,1]. При арифметической мутации к каждой координате с вероятностью P_m прибавляется случайное гауссово возмущение с масштабом 6% соответствующего диапазона. Затем значения обрезаются по границам допустимой области.')
    body(doc,'Элитизм переносит лучшего кандидата без изменения. Фиксированное число поколений даёт сопоставимую историю сходимости между запусками.')
    heading(doc,'3 АЛГОРИТМ И ПРОГРАММНАЯ РЕАЛИЗАЦИЯ',1,page=True)
    heading(doc,'3.1 Псевдокод',2)
    for line in ['1. Считать 18 проектов и перемешать индексы фиксированным seed.','2. Выделить 13 записей для обучения и 5 для теста.','3. Случайно создать популяцию пар (a,b) в установленных границах.','4. Для каждого кандидата вычислить E_f=aL^b и значение ED на обучающих строках.','5. Выбрать родителей рулеткой по весам, обратно связанным с ошибкой.','6. С вероятностью P_c выполнить арифметическое скрещивание; с вероятностью P_m мутировать каждую координату.','7. Ограничить параметры, сохранить элиту и повторить шаги 4–7 для всех поколений.','8. Выбрать наилучшую формулу по обучающей ED, оценить её на пяти отложенных проектах, сохранить таблицы и графики.']:
        p=body(doc,line,12.5,False);p.paragraph_format.left_indent=Cm(.6);p.paragraph_format.line_spacing=1.2
    heading(doc,'3.2 Параметры запуска',2)
    body(doc,'Выполнено 8 независимых запусков. В каждом использована популяция 120 решений, 600 поколений, P_c=0,90 и P_m=0,15. Начальное состояние генератора менялось между запусками. Для итоговой модели выбрана особь с минимальной обучающей ED среди восьми запусков; тестовые значения при выборе не использовались.')
    body(doc,'Таблица 2 фиксирует настройки и правила воспроизводимости эксперимента.')
    table(doc,'Таблица 2 — Параметры генетического алгоритма',['Параметр','Значение'],[
        ('Кодирование','Вещественная пара (a,b)'),('Размер популяции','120'),('Число поколений','600'),('Вероятность скрещивания P_c','0,90'),('Вероятность мутации P_m','0,15 на ген'),('Отбор','Рулеточный по преобразованным весам'),('Элитизм','1 лучший кандидат'),('Границы a','[0,05; 20]'),('Границы b','[0,1; 2,5]'),('Разбиение обуч./тест','13 / 5, seed=3'),('Независимые запуски','8; seeds 42–49')],[6.2,9.2],9.5)
    heading(doc,'4 РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА',1,page=True)
    g=SUMMARY['ga']; baseline=SUMMARY['log_linear_baseline']
    body(doc,f"Лучший из восьми запусков дал a={g['a']:.6f}, b={g['b']:.6f}; итоговая формула: {g['formula']}. Обучающая ED составила {g['training_metrics']['ED_RMS_person_months']:.3f} человеко-месяца. Во всех запусках найденные параметры близки друг к другу, что указывает на устойчивость данного поиска для выбранного обучающего набора.")
    body(doc,'На рисунке 1 показано снижение лучшей обучающей ошибки по поколениям. Таблица 3 содержит значения параметров и ED для каждого независимого запуска.')
    figure(doc,RESULTS/'convergence.png','Рисунок 1 — Сходимость лучшей обучающей ошибки ED',15.5)
    runs=SUMMARY['repeat_runs']
    table(doc,'Таблица 3 — Восемь независимых запусков',['Seed','a','b','ED обучения'],[(r['seed'],f"{r['a']:.6f}",f"{r['b']:.6f}",f"{r['train_ED']:.4f}") for r in runs],[2.3,4,4,4.5],9)
    body(doc,'Тестовая выборка содержит проекты №4, 6, 7, 9 и 16. Таблица 4 сопоставляет фактическую трудоёмкость и прогноз итоговой модели.')
    preds=list(csv.DictReader((RESULTS/'predictions.csv').open(encoding='utf-8-sig')))
    tests=[r for r in preds if r['split']=='test']
    table(doc,'Таблица 4 — Прогноз на тестовом множестве',['Проект','L','Факт, чел.-мес.','Прогноз GA','|Ошибка|'],[(r['project_id'],f"{float(r['kloc']):.1f}",f"{float(r['actual_effort']):.1f}",f"{float(r['ga_prediction']):.2f}",f"{float(r['ga_absolute_error']):.2f}") for r in tests],[1.6,2,3.5,3.5,3.5],8.5)
    body(doc,'Рисунок 2 сравнивает фактические и прогнозные значения на обучающих и тестовых проектах для генетической модели и лог-линейной базовой модели. Логарифмические оси позволяют увидеть обычные наблюдения рядом с необычно крупным значением проекта №4.')
    figure(doc,RESULTS/'actual_vs_predicted.png','Рисунок 2 — Фактические и прогнозные трудозатраты',15.5)
    metric_rows=[('GA, обучение',g['training_metrics']),('GA, тест (все 5)',g['test_metrics']),('GA, тест без проекта 4',g['test_metrics_excluding_project_4']),('Лог-линейная регрессия, обучение',baseline['training_metrics']),('Лог-линейная регрессия, тест',baseline['test_metrics'])]
    body(doc,'Таблица 5 сравнивает среднеквадратичную абсолютную ошибку ED и среднюю относительную ошибку MMRE. Для генетической модели отдельно показан тест без аномального проекта №4.')
    table(doc,'Таблица 5 — Сравнение качества модели',['Модель и множество','ED, чел.-мес.','MMRE, %'],[(name,f"{m['ED_RMS_person_months']:.3f}",f"{m['MMRE_percent']:.2f}") for name,m in metric_rows],[7.5,4,4],9)
    body(doc,'Тестовая ED велика из-за проекта №4 (факт 909,8; прогноз около 80,4). Без него ED остальных четырёх тестовых проектов равна 5,246 человеко-месяца. ')
    heading(doc,'КОНТРОЛЬНЫЕ ВОПРОСЫ',1,True,True)
    qa=[
        ('1. Приведите основную формулу методики COCOMO.','E_f=aL^b, где L — размер программного продукта в тысячах строк кода, а E_f — оценка трудоёмкости в человеко-месяцах. Коэффициенты a и b калибруются по историческим проектам.'),
        ('2. Какие данные необходимы для использования COCOMO?','Нужны размер проекта L и фактическая трудоёмкость E_f для проектов сравнимого класса. Для калибровки параметры подбираются по парам этих измерений.'),
        ('3. Что позволяет оценивать методика COCOMO?','Она оценивает трудоёмкость разработки программного обеспечения по размеру кода. Полученную оценку можно применять при планировании затрат и ресурсов.'),
        ('4. Какие данные можно использовать при обучении (поиске коэффициентов a,b)?','Набор исторических проектов с измеренными L и E_f. В этой работе использованы данные 18 проектов из таблицы 8.1.'),
        ('5. Как можно разбить данные на обучающее и тестовое множество?','Случайно разделить наблюдения на непересекающиеся подмножества, используя обучающую часть для настройки параметров, а тестовую — только для независимой оценки. В работе использовано 13 и 5 проектов соответственно.'),
        ('6. Какое кодирование потенциальных решений можно использовать в этой задаче?','Для генетического алгоритма — вещественную хромосому (a,b), как в варианте 4. Также возможно двоичное кодирование после дискретизации диапазонов параметров, но оно здесь не применяется.'),
        ('7. Какие типы генетических операторов можно использовать в этой задаче?','Отбор родителей, скрещивание и мутацию. В варианте 4 заданы рулеточный отбор, арифметическое скрещивание и арифметическая вещественная мутация.'),
        ('8. Какую фитнес-функцию можно использовать в этой задаче?','Для минимизации расхождения между измеренной и расчётной трудоёмкостью используется ED — корень из среднего квадрата абсолютных остатков в человеко-месяцах.'),
        ('9. Какие виды ошибок можно использовать в этой задаче?','Абсолютную (сумма модулей остатков), относительную (например, MRE/MMRE), среднеквадратичную ошибку и метрики разброса/объяснённой дисперсии. Выбор зависит от того, важнее ли абсолютная или относительная точность.'),
        ('10. Приведите формулу метрики абсолютных значений MD.','MD=Σᵢ|E_f,i−E_fm,i|, где E_f,i — фактическая трудоёмкость, а E_fm,i — рассчитанная моделью оценка i-го проекта.'),
        ('11. Приведите формулу средней относительной погрешности.','MMRE=(1/N)Σᵢ |E_f,i−E_fm,i|/|E_f,i|. В процентах результат умножается на 100. Наблюдения с нулевой фактической трудоёмкостью требуют отдельной обработки.'),
        ('12. Приведите формулу отклонения (дисперсии) из методички.','Согласно приведённым указаниям, VAF=[1−Var(E_f−E_fm)/Var(E_f)]·100%. Здесь Var — дисперсия соответствующих значений. В отчёте используется именно обозначение и формула из задания.'),
        ('13. Как можно улучшить методику COCOMO?','Калибровать параметры на актуальном и репрезентативном наборе, учитывать тип проекта и факторы сложности, проверять выбросы и качество измерений, разделять данные на обучение и тест, а качество оценивать несколькими метриками.'),
        ('14. Как применить роевой алгоритм для поиска a,b?','Положение частицы задать парой (a,b), а целевой функцией сделать ED на обучающих данных. Частицы перемещать по стандартным формулам PSO, ограничить параметры положительной областью и выбрать позицию с минимальной ошибкой.'),
        ('15. Как применить эволюционную стратегию для поиска a,b?','Начать с популяции вещественных векторов (a,b), создавать потомков рекомбинацией и мутацией, оценивать их по ED и формировать следующую популяцию отбором лучших. Повторять до достижения критерия остановки.'),
    ]
    for q,a in qa:
        p=doc.add_paragraph();p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Pt(2);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.25;p.paragraph_format.keep_with_next=True
        font(p.add_run(q),12.5,True)
        body(doc,'Ответ: '+a,12.5)
    body(doc,'Полный листинг генетического алгоритма и программы запуска приведён в приложении А.')
    heading(doc,'ЗАКЛЮЧЕНИЕ',1,True,True)
    body(doc,f"Выполнена калибровка модели COCOMO генетическим алгоритмом с вещественным кодированием и операторами варианта 4. Для итоговой формулы E_f={g['a']:.4f}·L^{g['b']:.4f} обучающая ED составила {g['training_metrics']['ED_RMS_person_months']:.3f} человеко-месяца.")
    body(doc,'На фиксированной тестовой выборке ошибка ED равна 370,937 человеко-месяца с проектом №4 и 5,246 без него. Большая разница вызвана исходным значением 909,8, перенесённым в отчёт как напечатано. Следовательно, вывод о качестве калибровки зависит от проверки качества исходных данных; аномальную строку следует уточнить у составителя таблицы, не подменяя её предположительным значением.')
    body(doc,'Восемь повторов дали близкие коэффициенты и обучающие ошибки, а лог-линейный ориентир показал сопоставимый результат. Эксперимент демонстрирует корректную работу генетической настройки, но малая выборка и выброс ограничивают обобщение результатов.')
    heading(doc,'СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ',1,True,True)
    for ref in [
        '1. Лабораторная работа № 8 «Эволюционные алгоритмы оценки стоимости проектов в программной инженерии»: методические указания. — Материал, предоставленный для выполнения работы.',
        '2. ГУАП. Для учебного процесса: нормативные требования и бланки титульных листов. — URL: https://guap.ru/c/regdocs/docs/uch (дата обращения: 10.11.2026).',
        '3. Boehm B. W. Software Engineering Economics. — Englewood Cliffs: Prentice-Hall, 1981.',
        '4. Haupt R. L., Haupt S. E. Practical Genetic Algorithms. 2nd ed. — Hoboken: John Wiley & Sons, 2004.',
    ]: body(doc,ref,12,False,WD_ALIGN_PARAGRAPH.JUSTIFY)
    heading(doc,'ПРИЛОЖЕНИЕ А',1,True,True)
    heading(doc,'Программный модуль генетического алгоритма',2,True)
    for filename in ['cocomo_ga.py','run_lab.py']:
        heading(doc,filename,2)
        for line in (ROOT/filename).read_text(encoding='utf-8').splitlines():
            p=doc.add_paragraph();p.paragraph_format.first_line_indent=Cm(0);p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.0;font(p.add_run(line or ' '),7,name='Consolas')
    doc.core_properties.title='Лабораторная работа 8, вариант 4 — настройка COCOMO генетическим алгоритмом'
    doc.core_properties.subject='Эволюционные методы проектирования программно-информационных систем'
    doc.save(ROOT/'report.docx')

if __name__=='__main__': main()
