from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image, ImageDraw, ImageFont
import sys

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT.parent / 'лр4' / 'lab_title.docx'
REPORT = ROOT / 'Отчет_ЛР5_вариант20.docx'
GRAPH = ROOT / 'Граф_КНА_вариант20.png'
SOURCE = ROOT / 'finite_automaton_synth.py'

ALPHABET = ['a', 'b', 'c', 'd', 'e']
STATES = ['q0', 'q1', 'q2', 'q3']
TRANSITIONS = {
    ('q0','a'):'q1', ('q1','b'):'q1', ('q1','c'):'q2', ('q1','d'):'q2', ('q1','e'):'q3',
    ('q2','c'):'q2', ('q2','d'):'q2', ('q2','e'):'q3', ('q3','e'):'q3',
}
ACCEPTING = {'q1','q2','q3'}


def set_font(run, size=14, bold=None, name='Times New Roman'):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn('w:ascii'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'), name)
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def clear_paragraph(p):
    for child in list(p._p):
        if child.tag != qn('w:pPr'):
            p._p.remove(child)


def page_field(p):
    r = p.add_run()
    for kind, val in [('begin',None),('instrText','PAGE'),('separate',None),('t','1'),('end',None)]:
        el = OxmlElement(f'w:{kind}' if kind in ('instrText','t') else 'w:fldChar')
        if kind in ('begin','separate','end'):
            el.set(qn('w:fldCharType'),kind)
        elif kind == 'instrText':
            el.set(qn('xml:space'),'preserve'); el.text=val
        else: el.text=val
        r._r.append(el)


def set_cell(cell, text, size=10, bold=False):
    cell.text = ''
    p=cell.paragraphs[0]
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Pt(0)
    p.paragraph_format.space_after=Pt(0)
    p.paragraph_format.line_spacing=1.0
    set_font(p.add_run(str(text)),size,bold)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_borders(table):
    pr=table._tbl.tblPr
    borders=pr.first_child_found_in('w:tblBorders')
    if borders is None:
        borders=OxmlElement('w:tblBorders'); pr.append(borders)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        el=OxmlElement(f'w:{edge}'); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'5'); el.set(qn('w:color'),'777777'); borders.append(el)


def add_table(doc, caption, headers, rows, size=10):
    p=doc.add_paragraph(); p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.space_before=Pt(5); p.paragraph_format.space_after=Pt(4)
    if caption.startswith('Таблица 3 —'):
        p.paragraph_format.page_break_before=True
    set_font(p.add_run(caption),11,True)
    t=doc.add_table(rows=1,cols=len(headers)); t.autofit=True; add_borders(t)
    for i,h in enumerate(headers): set_cell(t.rows[0].cells[i],h,size,True)
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row): set_cell(cells[i],v,size)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    return t


def body(doc,text,indent=True):
    p=doc.add_paragraph(style='Normal'); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent=Cm(1.25) if indent else Cm(0)
    p.paragraph_format.space_after=Pt(4)
    set_font(p.add_run(text),14)
    return p


def heading(doc,text,new_page=True):
    p=doc.add_paragraph(style='Heading 1'); p.paragraph_format.page_break_before=new_page
    p.paragraph_format.first_line_indent=Cm(0); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(12)
    set_font(p.add_run(text),14,True)
    return p


def draw_graph():
    im=Image.new('RGB',(1600,620),'white'); d=ImageDraw.Draw(im)
    try:
        f=ImageFont.truetype('C:/Windows/Fonts/times.ttf',34)
        fs=ImageFont.truetype('C:/Windows/Fonts/times.ttf',27)
    except OSError: f=fs=ImageFont.load_default()
    coords={'q0':(160,330),'q1':(560,330),'q2':(990,330),'q3':(1400,330)}; r=58
    def arrow(points,label,pos):
        d.line(points,fill='black',width=4)
        (x1,y1),(x2,y2)=points[-2],points[-1]
        import math
        a=math.atan2(y2-y1,x2-x1); tip=(x2,y2)
        left=(x2-19*math.cos(a)+9*math.sin(a),y2-19*math.sin(a)-9*math.cos(a))
        right=(x2-19*math.cos(a)-9*math.sin(a),y2-19*math.sin(a)+9*math.cos(a))
        d.polygon((tip,left,right),fill='black'); d.text(pos,label,fill='black',font=fs)
    d.line((40,330,100,330),fill='black',width=4); d.polygon(((100,330),(80,319),(80,341)),fill='black')
    for q,(x,y) in coords.items():
        d.ellipse((x-r,y-r,x+r,y+r),outline='black',width=4)
        if q in ACCEPTING: d.ellipse((x-r+9,y-r+9,x+r-9,y+r-9),outline='black',width=3)
        box=d.textbbox((0,0),q,font=f); d.text((x-(box[2]-box[0])/2,y-(box[3]-box[1])/2-4),q,fill='black',font=f)
    arrow([(218,330),(502,330)],'a/1',(332,277))
    def loop(x,label):
        d.arc((x-48,190,x+48,285),180,360,fill='black',width=4)
        d.line((x+48,237,x+35,292),fill='black',width=4); d.polygon(((x+35,292),(x+28,271),(x+46,276)),fill='black')
        d.text((x-45,163),label,fill='black',font=fs)
    loop(560,'b/1'); arrow([(618,330),(932,330)],'c/1, d/1',(713,275)); loop(990,'c/1, d/1')
    arrow([(1048,330),(1342,330)],'e/1',(1153,275)); loop(1400,'e/1')
    arrow([(610,373),(680,475),(850,500),(930,385)],'e/1',(759,479))
    im.save(GRAPH)


def build():
    draw_graph()
    doc=Document(str(TEMPLATE)); sec=doc.sections[0]
    sec.top_margin= Cm(2); sec.bottom_margin=Cm(2); sec.left_margin=Cm(3); sec.right_margin=Cm(1.5)
    sec.different_first_page_header_footer=True
    normal=doc.styles['Normal']; normal.font.name='Times New Roman'; normal.font.size=Pt(14)
    normal._element.rPr.rFonts.set(qn('w:ascii'),'Times New Roman'); normal._element.rPr.rFonts.set(qn('w:hAnsi'),'Times New Roman'); normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
    normal.paragraph_format.first_line_indent=Cm(1.25); normal.paragraph_format.line_spacing=1.5; normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for style_name in ('Heading 1','Heading 2'):
        st=doc.styles[style_name]; st.font.name='Times New Roman'; st.font.size=Pt(14); st.font.bold=True
        st._element.rPr.rFonts.set(qn('w:ascii'),'Times New Roman'); st._element.rPr.rFonts.set(qn('w:hAnsi'),'Times New Roman'); st._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
        st.paragraph_format.keep_with_next=True
    foot=sec.footer.paragraphs[0]; clear_paragraph(foot); foot.alignment=WD_ALIGN_PARAGRAPH.CENTER; page_field(foot)
    # GUAP official title page form retained from the prior lab package.
    for i,text in ((1,'КАФЕДРА № 43'),(7,'Санкт-Петербург 2026')):
        doc.paragraphs[i].text=text; doc.paragraphs[i].alignment=WD_ALIGN_PARAGRAPH.CENTER
        doc.paragraphs[i].paragraph_format.first_line_indent=Pt(0); doc.paragraphs[i].paragraph_format.line_spacing=1
        for r in doc.paragraphs[i].runs: set_font(r,14)
    for i in (2,3): doc.paragraphs[i].paragraph_format.first_line_indent=Pt(0); doc.paragraphs[i].paragraph_format.line_spacing=1
    set_cell(doc.tables[0].cell(0,4),'Рогачев С. А.',10); set_cell(doc.tables[0].cell(1,4),'инициалы, фамилия',9)
    title=doc.tables[1]
    set_cell(title.cell(0,0),'ОТЧЕТ О ЛАБОРАТОРНОЙ РАБОТЕ № 5',13,True)
    set_cell(title.cell(1,0),'Исследование алгоритмов синтеза конечных автоматов\nВариант 20',11)
    set_cell(title.cell(2,0),'по курсу: Теория вычислительных процессов',10)
    for row in list(title.rows)[3:]: title._tbl.remove(row._tr)
    set_cell(doc.tables[2].cell(0,1),'4332',12); set_cell(doc.tables[2].cell(0,5),'Могилатов С. И.',12)
    set_cell(doc.tables[2].cell(1,3),'подпись, дата',9); set_cell(doc.tables[2].cell(1,5),'инициалы, фамилия',9)
    doc.add_page_break()

    heading(doc,'СОДЕРЖАНИЕ',False)
    for label,page in [('Цель работы','3'),('Постановка задачи','4'),('Алгоритм синтеза КНА','5'),('Процесс синтеза КНА','7'),('Программа на языке Python','9'),('Выходной файл программы','10'),('Конечный автомат тремя способами','11'),('Вывод','13'),('Контрольные вопросы','14'),('Список литературы','16'),('Приложение А. Исходный код','17')]:
        p=doc.add_paragraph(); p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.left_indent=Cm(1); p.paragraph_format.line_spacing=1.2
        set_font(p.add_run(f'{label} ................................................ {page}'),12)

    heading(doc,'ЦЕЛЬ РАБОТЫ')
    body(doc,'Изучить алгоритм синтеза конечного автомата для проверки принадлежности входного слова регулярному выражению, выполнить разметку мест и построить автомат для варианта 20. Реализовать алгоритм на языке Python и представить полученный автомат матрицами и ориентированным графом.')

    heading(doc,'ПОСТАНОВКА ЗАДАЧИ')
    body(doc,'Вариант 20. Регулярное выражение: a⟨b⟩⟨(c|d)⟩⟨e⟩. Угловые скобки обозначают повторение заключённого фрагмента ноль или более раз; вертикальная черта задаёт альтернативу.')
    body(doc,'Требуется построить КНА, распознающий это выражение, показать этапы синтеза, реализовать программу высокого уровня, которая читает регулярное выражение из текстового файла и записывает матрицу синтезированного автомата в файл.')
    body(doc,'Язык состоит из слов, начинающихся символом a, после которого идут ноль или более b, затем ноль или более символов c или d, а в конце — ноль или более e. Каждая повторяемая часть может быть пустой. Примеры допустимых слов: a, ab, acd, ade, abbbcd, abceee. Недопустимы пустая строка, ba, acb и aeb.')

    heading(doc,'АЛГОРИТМ СИНТЕЗА КНА')
    body(doc,'Место регулярного выражения — позиция между соседними символами выражения, а также позиция перед первым и после последнего символа. Для наглядности в выражение вставляются вертикальные черты. Основное место получает основной индекс; начальное место перед первым символом имеет индекс 0. Индексы основных мест распространяются по отношению подчинения как неосновные индексы.')
    body(doc,'Правила подчинения мест:')
    for text in [
        'Открывающая скобка: начальные места всех термов внутри обычной или итерационной группы подчиняются месту непосредственно слева от открывающей скобки.',
        'Закрывающая скобка: место непосредственно справа от закрывающей скобки подчиняется конечным местам термов внутри группы; для итерационной группы оно также подчинено месту слева от открывающей скобки.',
        'Итерационная группа: начальные места всех её термов подчиняются месту непосредственно справа от закрывающей скобки.',
        'Транзитивность: если место A подчинено B, а B подчинено C, то A подчинено C.',
        'Рефлексивность: каждое место подчинено самому себе. Другие отношения подчинения не вводятся.'
    ]:
        p=doc.add_paragraph(style='Normal'); p.paragraph_format.left_indent=Cm(1.25); p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.line_spacing=1.3
        set_font(p.add_run('• '+text),13)
    body(doc,'Состояние автомата — подмножество основных индексов, активных в текущей точке обработки. Основные индексы и выражения, чьи конечные места им подчинены, служат метками состояний. Начальному состоянию соответствует индекс 0. Для каждого входного символа в текущем состоянии собираются индексы основных мест, следующих за местами, отмеченными индексами состояния; повторяющиеся индексы объединяются. Пустое множество означает отсутствие перехода. Состояние является конечным, если в его метку входит индекс конечного места регулярного выражения.')
    body(doc,'Программа вычисляет множество следующих мест для каждого символа, детерминирует переходы и объединяет эквивалентные состояния с одинаковым дальнейшим поведением. Специальное конечное место # отмечает завершение выражения; оно не входит во входной алфавит. Объединение эквивалентных состояний соответствует совместной метке индексов в состоянии и позволяет получить компактную таблицу, как в примере методички.')

    heading(doc,'ПРОЦЕСС СИНТЕЗА КНА')
    body(doc,'Размеченное выражение варианта 20: |a|⟨|b|⟩⟨(|c|||d|)⟩⟨|e|⟩. Основные индексы назначаются начальному месту и позициям после букв; промежуточные места вокруг скобок и альтернативы участвуют в отношениях подчинения.')
    add_table(doc,'Таблица 1 — Основные места выражения',['Место','Основной индекс','Символ после места'],[
        ('1','0','a'),('2','1','⟨'),('4','2','⟩'),('8','3','|'),('10','4',')'),('14','5','⟩')],10)
    body(doc,'Для компактного вычисления переходов приведены следующие места после букв и их места-преемники после раскрытия подчинения и транзитивности. Знак # обозначает конечное место, соответствующее концу выражения.')
    add_table(doc,'Таблица 2 — Связи основных мест со следующими местами',['Основное место','Символ','Следующие места'],[
        ('1','a','2, 3, 4, 5, #'),('2','b','2, 3, 4, 5, #'),('3','c','3, 4, 5, #'),('4','d','3, 4, 5, #'),('5','e','5, #')],10)
    body(doc,'После a автомат может продолжить b-цикл, перейти к c/d-циклу или сразу начать e-цикл; конечное место # показывает, что слово a уже допустимо. После b возможны те же продолжения. После c или d автомат остаётся в цикле c/d либо переходит к e. После e допускается только дальнейший символ e. Поэтому активные места сводятся к четырём состояниям: q0={0}, q1={1,2}, q2={3,4}, q3={5}. Индексы в фигурных скобках — объединённые основные индексы после соответствующего этапа; q1–q3 конечные.')
    add_table(doc,'Таблица 3 — Множества состояний',['Состояние','Основные индексы','Смысл','Конечное'],[
        ('q0','{0}','Начало, ожидается a','Нет'),('q1','{1, 2}','Прочитан a; продолжается b*','Да'),('q2','{3, 4}','Читается блок (c|d)*','Да'),('q3','{5}','Читается завершающий блок e*','Да')],9)
    body(doc,'Матрица переходов строится для каждого состояния и каждого символа алфавита X={a,b,c,d,e}. Если следующего места для символа нет, переход обозначается прочерком.')
    transition_rows=[[q]+[TRANSITIONS.get((q,x),'—') for x in ALPHABET] for q in STATES]
    add_table(doc,'Таблица 4 — Матрица переходов',['Q\\X',*ALPHABET],transition_rows,10)

    heading(doc,'ПРОГРАММА НА ЯЗЫКЕ PYTHON')
    body(doc,'Программа finite_automaton_synth.py считывает выражение из UTF-8-файла, разбирает символы, альтернативы, группы и повторения ⟨…⟩, нумерует места, вычисляет множества последующих мест, строит детерминированный автомат, объединяет эквивалентные состояния и записывает матрицу в указанный текстовый файл. Запуск из корня репозитория:')
    p=doc.add_paragraph(); p.paragraph_format.left_indent=Cm(1); p.paragraph_format.first_line_indent=Cm(0)
    set_font(p.add_run('python лр5/finite_automaton_synth.py лр5/data/variant20.regex -o лр5/output/variant20_automaton.txt'),10)
    body(doc,'Полный текст программы приведён в приложении А.')

    heading(doc,'ВЫХОДНОЙ ФАЙЛ ПРОГРАММЫ')
    body(doc,'Содержимое файла variant20_automaton.txt, созданного программой для варианта 20:')
    output_text=(ROOT/'output'/'variant20_automaton.txt').read_text(encoding='utf-8').splitlines()
    for line in output_text:
        p=doc.add_paragraph(); p.paragraph_format.left_indent=Cm(0.5); p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.line_spacing=1.0; p.paragraph_format.space_after=Pt(0)
        set_font(p.add_run(line),9)

    heading(doc,'КОНЕЧНЫЙ АВТОМАТ ТРЕМЯ СПОСОБАМИ')
    body(doc,'Первое представление — матрицы переходов и выходов автомата Мили. Входной алфавит X={a,b,c,d,e}, множество состояний Q={q0,q1,q2,q3}, начальное состояние q0. Выход 1 на дуге означает, что после чтения символа автомат находится в допускающем состоянии; недопустимый переход не имеет выхода.')
    add_table(doc,'Таблица 5 — Таблица переходов δ',['Q\\X',*ALPHABET],[[q]+[TRANSITIONS.get((q,x),'—') for x in ALPHABET] for q in STATES],10)
    add_table(doc,'Таблица 6 — Таблица выходов λ',['Q\\X',*ALPHABET],[[q]+[('1' if TRANSITIONS.get((q,x)) in ACCEPTING else '0') if TRANSITIONS.get((q,x)) else '—' for x in ALPHABET] for q in STATES],10)
    body(doc,'Второе представление — ориентированный граф переходов. Начальное состояние обозначено входящей стрелкой, двойные окружности показывают допускающие состояния, метки дуг имеют вид вход/выход.')
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent=Cm(0)
    p.add_run().add_picture(str(GRAPH),width=Cm(16))
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.first_line_indent=Cm(0); set_font(p.add_run('Рисунок 1 — Граф синтезированного КНА для варианта 20'),11)
    body(doc,'Третье представление — автоматная матрица: строки задают исходные состояния, столбцы — символы; ячейка содержит целевое состояние и выход. Она непосредственно соответствует выходному файлу программы.')
    add_table(doc,'Таблица 7 — Автоматная матрица',['Q\\X',*ALPHABET],[[q]+[f"{TRANSITIONS[(q,x)]}/1" if (q,x) in TRANSITIONS else '—' for x in ALPHABET] for q in STATES],10)
    checks=[('a','q0 → q1','1','Допустимо'),('abbb','q0 → q1 → q1 → q1 → q1','1, 1, 1, 1','Допустимо'),('acd','q0 → q1 → q2 → q2','1, 1, 1','Допустимо'),('ade','q0 → q1 → q2 → q3','1, 1, 1','Допустимо'),('abceee','q0 → q1 → q1 → q2 → q3 → q3 → q3','1, 1, 1, 1, 1, 1','Допустимо'),('','q0','—','Недопустимо'),('ba','q0 (нет перехода по b)','—','Недопустимо'),('acb','q0 → q1 → q2 (нет перехода по b)','1, 1, —','Недопустимо'),('aeb','q0 → q1 → q3 (нет перехода по b)','1, 1, —','Недопустимо')]
    add_table(doc,'Таблица 8 — Проверка допустимости слов',['Слово','Траектория','Выходы','Результат'],checks,8)
    body(doc,'Таблицы, граф и автоматная матрица содержат один набор переходов. Проверки подтверждают, что автомат принимает слова из выражения, в том числе a, где все повторяемые части пусты, и отклоняет слова с неверным порядком символов.')

    heading(doc,'ВЫВОД')
    body(doc,'Для варианта 20 по регулярному выражению a⟨b⟩⟨(c|d)⟩⟨e⟩ построен конечный автомат, реализующий алгоритм синтеза по местам и их подчинению. Получены четыре состояния, переходы для алфавита {a,b,c,d,e}, матрицы переходов и выходов, ориентированный граф и автоматная матрица.')
    body(doc,'Программа на Python читает выражение из файла и записывает результат синтеза в текстовую матрицу. Контрольные слова подтверждают корректную обработку альтернативы, порядка блоков и нулевого числа повторов.')

    heading(doc,'КОНТРОЛЬНЫЕ ВОПРОСЫ')
    questions=[
        ('1. Что такое синтез конечного автомата?','Это построение конечного множества состояний и функции переходов по заданному формальному описанию языка, чтобы автомат распознавал ровно его слова.'),
        ('2. Что такое место регулярного выражения?','Позиция между символами выражения, а также начальная и конечная позиции.'),
        ('3. Как обозначаются места?','Между символами и по краям выражения ставятся вертикальные черты; полученные места нумеруются.'),
        ('4. Сформулируйте правило открывающих скобок.','Начальные места каждого терма внутри группы подчиняются месту непосредственно слева от открывающей скобки.'),
        ('5. Сформулируйте правило закрывающих скобок.','Место справа от закрывающей скобки подчиняется конечным местам термов внутри группы; для итерационной скобки оно также подчиняется месту слева от открывающей скобки.'),
        ('6. Сформулируйте правило итерационных скобок.','Начальные места всех термов внутри итерационной группы подчиняются месту справа от закрывающей скобки.'),
        ('7. Сформулируйте правило транзитивности.','Если A подчинено B, а B подчинено C, то A подчинено C.'),
        ('8. Сформулируйте правило рефлексивности.','Каждое место подчинено самому себе.'),
        ('9. Что такое основной индекс?','Основной индекс — натуральный номер, назначенный основному месту; начальное место получает индекс 0.'),
        ('10. Что такое неосновной индекс?','Это основной индекс, распространённый на другие места, подчинённые месту с этим основным индексом.'),
        ('11. Как формируется таблица переходов?','Для состояния и входного символа выбираются основные места, следующие за местами, отмеченными индексами состояния; их индексы объединяются в множество целевого состояния. При отсутствии таких мест переход пуст.'),
        ('12. Как определить конечные состояния?','Состояние конечное, если в него входит индекс, связанный с конечным местом регулярного выражения; в данной работе это q1, q2 и q3, что также отражает возможность завершить каждый цикл.')]
    for q,a in questions:
        p=doc.add_paragraph(); p.paragraph_format.keep_with_next=True; p.paragraph_format.first_line_indent=Cm(0); set_font(p.add_run(q),12,True)
        body(doc,a)

    heading(doc,'СПИСОК ЛИТЕРАТУРЫ')
    refs=[
        '1. Вавилов Е. Н., Портной Г. П. Синтез схем электронных цифровых машин. — М.: Советское радио, 1963. — 440 с.',
        '2. Гордеев А. В., Молчанов А. Ю. Системное программное обеспечение. — СПб.: Питер, 2001. — 736 с.',
        '3. Хантер Р. Проектирование и конструирование компиляторов. — М.: Финансы и статистика, 1984. — 232 с.',
        '4. Ахо А., Лам М., Сети Р., Ульман Дж. Компиляторы. Принципы, технологии и инструментарий. — М.: Вильямс, 2008. — 1184 с.',
        '5. Лабораторная работа № 5 «Исследование алгоритмов синтеза конечных автоматов». Методические указания. — 7 с.'
    ]
    for item in refs: body(doc,item)

    heading(doc,'ПРИЛОЖЕНИЕ А. ИСХОДНЫЙ КОД ПРОГРАММЫ')
    body(doc,'Листинг программы finite_automaton_synth.py.',False)
    for line in SOURCE.read_text(encoding='utf-8-sig').splitlines():
        p=doc.add_paragraph(); p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.left_indent=Cm(0); p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing=1.0
        set_font(p.add_run(line if line else ' '),8.5,name='Consolas')
    doc.save(REPORT)
    print(REPORT)

if __name__=='__main__': build()
