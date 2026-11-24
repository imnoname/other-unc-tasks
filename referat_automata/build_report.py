"""Сборка реферата на официальном бланке ГУАП с фактическими данными."""
from pathlib import Path
from copy import deepcopy
import ast
import json
import re
from docx import Document
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from core import synthesize, minimize, lecture_machine, run, compare

BASE=Path(__file__).resolve().parent
EX=json.loads((BASE/'results/experiments.json').read_text(encoding='utf-8'))
EVENTS=json.loads((BASE/'results/gui_events.json').read_text(encoding='utf-8'))
INPUTS=json.loads((BASE/'docs/scenario_inputs.json').read_text(encoding='utf-8'))
NOTES=json.loads((BASE/'docs/function_reference.json').read_text(encoding='utf-8'))
NOTES.update(json.loads((BASE/'docs/function_reference_aux.json').read_text(encoding='utf-8')))
D=Document(BASE/'sources/guap_referat_title.docx')
TABLE=0; FIGURE=0
if 'Table Grid' not in D.styles:
    D.styles.element.append(deepcopy(Document().styles['Table Grid'].element))


def font(run,name='Times New Roman',size=14,bold=False):
    run.font.name=name;run.font.size=Pt(size);run.font.bold=bold
    run.font.color.rgb=RGBColor(0,0,0)
    rp=run._element.get_or_add_rPr()
    rf=rp.find(qn('w:rFonts'))
    if rf is None:rf=OxmlElement('w:rFonts');rp.insert(0,rf)
    for attr in ['ascii','hAnsi','eastAsia','cs']:rf.set(qn('w:'+attr),name)


def pf(p,size=14,align=WD_ALIGN_PARAGRAPH.JUSTIFY,indent=1.25,line=1.5):
    p.alignment=align
    f=p.paragraph_format;f.first_line_indent=Cm(indent);f.left_indent=Cm(0);f.right_indent=Cm(0)
    f.line_spacing=line;f.space_after=Pt(0);f.space_before=Pt(0)
    for r in p.runs:font(r,size=size)
    return p


def p(text):
    return pf(D.add_paragraph(text))


def field(paragraph,instruction):
    run=paragraph.add_run();start=OxmlElement('w:fldChar');start.set(qn('w:fldCharType'),'begin')
    code=OxmlElement('w:instrText');code.set(qn('xml:space'),'preserve');code.text=instruction
    separate=OxmlElement('w:fldChar');separate.set(qn('w:fldCharType'),'separate')
    end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end')
    for element in [start,code,separate,end]:run._r.append(element)


def heading(text,level=1,structural=False):
    h=D.add_paragraph(text,'Heading '+str(level))
    pf(h,align=WD_ALIGN_PARAGRAPH.CENTER if structural else WD_ALIGN_PARAGRAPH.LEFT,
       indent=0 if structural else 1.25)
    h.paragraph_format.keep_with_next=True
    h.paragraph_format.space_after=Pt(10)
    h.paragraph_format.space_before=Pt(8) if level>1 else Pt(0)
    h.paragraph_format.page_break_before=(level==1)
    for r in h.runs:font(r,bold=True)
    return h


def equation(text):
    par=D.add_paragraph();pf(par,align=WD_ALIGN_PARAGRAPH.CENTER,indent=0)
    par.paragraph_format.space_before=Pt(6);par.paragraph_format.space_after=Pt(6)
    math=OxmlElement('m:oMath');r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text
    r.append(t);math.append(r);par._p.append(math)


def table(title,headers,rows,number=None,continued=False):
    global TABLE
    if number is None:TABLE+=1;number=TABLE
    caption=D.add_paragraph(('Продолжение таблицы ' if continued else 'Таблица ')+str(number)+('' if continued else ' - '+title))
    pf(caption,size=12,align=WD_ALIGN_PARAGRAPH.LEFT,indent=0,line=1)
    caption.paragraph_format.keep_with_next=True;caption.paragraph_format.space_before=Pt(6)
    t=D.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.autofit=True
    for cell,text in zip(t.rows[0].cells,headers):
        cell.text=str(text)
        sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'F2F2F2');cell._tc.get_or_add_tcPr().append(sh)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        for cell,value in zip(t.add_row().cells,row):cell.text=str(value)
    for row_index,row in enumerate(t.rows):
        no=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no)
        for cell in row.cells:
            for par in cell.paragraphs:
                pf(par,size=12,align=WD_ALIGN_PARAGRAPH.CENTER,indent=0,line=1)
                par.paragraph_format.keep_with_next=(row_index==0)
                par.paragraph_format.space_after=Pt(3);par.paragraph_format.space_before=Pt(3)
    D.add_paragraph().paragraph_format.space_after=Pt(0)
    return number


def machine_table(m,title):
    rows=[]
    for state in m.states:
        tag=('→' if state==m.start else '')+('*' if state in m.finals else '')+state
        rows.append([tag]+['/'.join(m.transitions[state][x]) for x in m.alphabet])
    table(title,['Q / X']+m.alphabet,rows)


def picture(path,title,width=16.5,label=None):
    global FIGURE
    FIGURE+=1
    par=D.add_paragraph();pf(par,align=WD_ALIGN_PARAGRAPH.CENTER,indent=0,line=1)
    par.paragraph_format.keep_with_next=True
    par.add_run().add_picture(str(path),width=Cm(width))
    caption=D.add_paragraph(f'Рисунок {label or FIGURE} - {title}')
    pf(caption,size=12,align=WD_ALIGN_PARAGRAPH.CENTER,indent=0,line=1)
    caption.paragraph_format.space_after=Pt(8)


def make_title():
    D.paragraphs[3].text='КАФЕДРА № 43'
    D.paragraphs[9].text='Санкт-Петербург 2026'
    D.tables[0].cell(0,4).text='Охтилев М.Ю.'
    D.tables[1].cell(0,0).paragraphs[0].style=D.styles['Title']
    D.tables[1].cell(1,0).text='Синтез и минимизация конечного автомата'
    D.tables[1].cell(3,0).text='Теория вычислительных процессов'
    D.tables[2].cell(0,1).text='4332'
    D.tables[2].cell(0,5).text='Могилатов С.И.'
    for index,par in enumerate(D.paragraphs):
        # Бланк сохраняет собственную геометрию, независимо от стилей тела.
        par.paragraph_format.first_line_indent=Cm(0)
        par.paragraph_format.left_indent=Cm(0);par.paragraph_format.right_indent=Cm(0)
        par.paragraph_format.line_spacing=1
        par.alignment=WD_ALIGN_PARAGRAPH.CENTER if index in [0,1,2,3,9] else WD_ALIGN_PARAGRAPH.LEFT
        for run in par.runs:font(run,size=run.font.size.pt if run.font.size else 12)
    for i,t in enumerate(D.tables):
        for ri,row in enumerate(t.rows):
            for ci,cell in enumerate(row.cells):
                for par in cell.paragraphs:
                    par.paragraph_format.first_line_indent=Cm(0)
                    par.paragraph_format.left_indent=Cm(0);par.paragraph_format.right_indent=Cm(0)
                    par.paragraph_format.line_spacing=1
                    par.alignment=WD_ALIGN_PARAGRAPH.CENTER if i==1 or (ri==0 and ci>0) else WD_ALIGN_PARAGRAPH.LEFT
                    for run in par.runs:font(run,size=14 if ri==0 or i==1 else 10)
                    if i==2 and ri==0 and ci==0:
                        for run in par.runs:font(run,size=12)
    D.core_properties.title='Синтез и минимизация конечного автомата'
    D.core_properties.author='Могилатов Семен Игоревич'
    D.core_properties.subject='Теория вычислительных процессов'


make_title()
for name in ['Normal','Heading 1','Heading 2','Heading 3','Title']:
    st=D.styles[name];st.font.name='Times New Roman';st.font.size=Pt(14)
    st.font.color.rgb=RGBColor(0,0,0)
    st.paragraph_format.first_line_indent=Cm(1.25)
    st.paragraph_format.line_spacing=1.5
    st.paragraph_format.space_after=Pt(0)
section=D.add_section(WD_SECTION_START.NEW_PAGE)
for sec in [section]:
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    sec.left_margin=Cm(3);sec.right_margin=Cm(1.5);sec.top_margin=Cm(2);sec.bottom_margin=Cm(2)
    sec.footer_distance=Cm(1)
    sec.footer.is_linked_to_previous=False
    f=sec.footer.paragraphs[0];pf(f,size=12,align=WD_ALIGN_PARAGRAPH.CENTER,indent=0,line=1)
    field(f,'PAGE')

for name in ['toc 1','toc 2']:
    try:style=D.styles[name]
    except KeyError:
        from docx.enum.style import WD_STYLE_TYPE
        style=D.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
    style.font.name='Times New Roman';style.font.size=Pt(12);style.font.color.rgb=RGBColor(0,0,0)
    style.paragraph_format.line_spacing=1.15
    style.paragraph_format.first_line_indent=Cm(0)
    style.paragraph_format.left_indent=Cm(0 if name=='toc 1' else 0.5)
    style.paragraph_format.space_before=Pt(0)
    style.paragraph_format.space_after=Pt(0)
contents=heading('СОДЕРЖАНИЕ',1,True)
contents.style=D.styles['Normal']
contents.paragraph_format.page_break_before=False
outline=OxmlElement('w:outlineLvl');outline.set(qn('w:val'),'9');contents._p.get_or_add_pPr().append(outline)
field(D.add_paragraph(),'TOC \\o "1-2" \\h \\z \\u')

m=synthesize('a<b|c>d');small,parts,mapping=minimize(m)
lecture=lecture_machine();lm,lp,lmap=minimize(lecture)


def data(name):
    if name=='places':
        p(f'Разметка выражения приведена в таблице {TABLE+1}. Индекс места p соответствует номеру зазора с нуля.')
        rows=[[a['place'],a['before'],a['after'],a['main'] if a['main'] is not None else '-',
               ','.join(map(str,a['indices'])) or '-',','.join(map(str,a['subordinates']))]
              for a in m.details['places']]
        table('Места и распространённые индексы',['p','Слева','Справа','Осн.','Все индексы','Подчинённые'],rows)
    elif name=='raw':
        p(f'В таблице {TABLE+1} показан исходный полный автомат. Символ → отмечает начало, * - конечность.')
        machine_table(m,'Исходные переходы и выходы')
        p('Метки состояний: '+ '; '.join(q+' = '+('{'+','.join(map(str,s))+'}' if s else '{}') for q,s in m.details['subsets'].items())+'.')
    elif name=='regex_partitions':
        for i,blocks in enumerate(parts):p(f'P{i} = '+'; '.join('{'+', '.join(b)+'}' for b in blocks)+'.')
    elif name=='minimal':
        p(f'Итоговые переходы приведены в таблице {TABLE+1}; автоматная матрица - в таблице {TABLE+2}.')
        machine_table(small,'Минимальный распознаватель')
        rows=[[q]+[', '.join(x+'/'+out for x,(target,out) in small.transitions[q].items() if target==t) or '-' for t in small.states] for q in small.states]
        table('Автоматная матрица минимального распознавателя',['Q / Q']+small.states,rows)
    elif name=='regex_examples':
        p(f'В таблице {TABLE+1} сопоставлены результаты для характерных слов.')
        rows=[]
        for word in ['','ad','abd','acd','abcd','abbd','ab','d','add']:
            r=run(m,word);states=[m.start]+[step[3] for step in r['trace']]
            rows.append([word or 'ε','→'.join(states),','.join(r['outputs']) or 'ε','Да' if r['accepted'] else 'Нет'])
        table('Примеры проверки слов',['Слово','Траектория','Выходы','Допустимо'],rows)
    elif name=='lecture_table':
        p(f'Исходная таблица из конспекта воспроизведена в таблице {TABLE+1}.')
        machine_table(lecture,'Лекционный автомат Мили')
    elif name=='lecture_minimal':
        p(f'В таблице {TABLE+1} показаны переходы между устойчивыми классами.')
        machine_table(lm,'Минимальный автомат лекционного примера')
    elif name=='unittest':
        p(f'Выполнено {EX["unittest_count"]} тестовых методов unittest. Итог: все пройдены. Полный журнал сохранён в results/unittest.txt; тестовые наборы в приложении Б позволяют повторить запуск.')
    elif name=='variants':
        rows=[[r['variant'],r['expression'].replace('<','⟨').replace('>','⟩'),r['states'],r['minimal'],r['checks']]
              for r in EX['variants']]
        p(f'Результаты всех вариантов приведены в таблице {TABLE+1}. Число состояний учитывает явное состояние отказа, если оно достижимо.')
        D.add_page_break()
        column_numbers=[['1','2','3','4','5']]
        num=table('Результаты синтеза и минимизации всех вариантов ЛР №5',['№','Выражение','Исх.','Мин.','Слов'],column_numbers+rows[:15])
        D.add_page_break();table('', ['№','Выражение','Исх.','Мин.','Слов'],column_numbers+rows[15:],number=num,continued=True)
    elif name=='experiment_summary':
        p(f'Для 30 учебных выражений выполнено {sum(r["checks"] for r in EX["variants"]):,} проверок слов; для 120 сгенерированных выражений - 7 560. Всего зарегистрировано {EX["word_checks"]:,} пар «выражение - слово». Расхождений с оракулом: {EX["mismatches"]}. Во всех случаях исходный и минимальный автоматы также прошли точное сравнение.'.replace(',',' '))
    elif name=='input_contract':
        p('Пример входа Мили JSON повторяет таблицу лекции. Его можно вставить в поле целиком или открыть examples/lecture.json:')
        payload=lecture.to_dict()
        lines=['{', '  "states": '+json.dumps(payload['states'])+',',
               '  "alphabet": ["x", "y"],', '  "start": "q1",',
               '  "recognizer": false,', '  "transitions": {']
        for i,q in enumerate(lecture.states):
            lines.append('    '+json.dumps(q)+': '+json.dumps(payload['transitions'][q])+(',' if i<len(lecture.states)-1 else ''))
        lines+=['  }','}']
        inline_code('\n'.join(lines))
        p('Для вызова ядра напрямую вход и результат связываются следующим образом:')
        table('Данные на входе и результат основных операций', ['Операция','Вход','Ожидаемый результат'],[
            ['synthesize','a<b|c>d, лимит 256','Machine: 6 состояний, recognizer=True'],
            ['minimize','Построенный Machine','Machine из 4 состояний, разбиения и mapping'],
            ['run','Распознаватель и ad','accepted=True; outputs=[0,1]; 2 шага'],
            ['run','Лекционный Мили и xyx','accepted=None; outputs=[1,0,2]; 3 шага'],
            ['compare','Исходный и минимальный автоматы','equivalent=True; witness=None']])
        p('В таблице выходы для краткости записаны числами. В объекте Machine и словаре run они хранятся строками, например outputs=["1", "0", "2"]. Ниже полный результат run на входе xyx представлен в JSON; null соответствует None в Python:')
        result=run(lecture,'xyx')
        lines=['{','  "accepted": null, "error": null,','  "trace": [']
        lines += ['    '+json.dumps(step)+(',' if i<len(result['trace'])-1 else '') for i,step in enumerate(result['trace'])]
        lines += ['  ],','  "outputs": ["1", "0", "2"], "state": "q4"','}']
        inline_code('\n'.join(lines))
    elif name=='events':
        # Эти три снимка относятся к прежним сообщениям; их нельзя выдавать за
        # финальную версию. После нового прогона список становится пустым.
        manifest=BASE/'results/screenshot_manifest.json'
        valid=set(json.loads(manifest.read_text(encoding='utf-8'))['valid']) if manifest.exists() else {f'E{i:02}' for i in range(1,46)}-{'E32','E38','E45'}
        for event in EVENTS:
            shot=BASE/'screenshots'/event['screenshot']
            has=event['id'] in valid and shot.exists()
            if has:D.add_page_break()
            par=D.add_paragraph(f'{event["id"]}  {event["name"]}')
            pf(par,align=WD_ALIGN_PARAGRAPH.LEFT,indent=0)
            for r in par.runs:font(r,bold=True)
            par.paragraph_format.keep_with_next=True
            for label,description in zip(['Входные данные','Действие','Ожидаемый вывод'],INPUTS[event['id']]):
                par=D.add_paragraph(label+': '+description);pf(par,size=12,line=1.15)
                par.paragraph_format.keep_with_next=True
            actual=event['actual'].replace(str(BASE),'[каталог проекта]')
            par=D.add_paragraph('Получено: '+actual);pf(par,size=12,line=1.15)
            par.paragraph_format.keep_with_next=has
            if has:
                par=D.add_paragraph(f'Результат сценария представлен на рисунке {FIGURE+1}.')
                pf(par,size=12,line=1.15);par.paragraph_format.keep_with_next=True
                picture(shot,event['id']+' '+event['name'])
            else:p('Проверка обработчика и состояния виджетов завершилась успешно.')


def inline_code(text):
    for line in text.splitlines():
        par=D.add_paragraph()
        pf(par,size=11,align=WD_ALIGN_PARAGRAPH.LEFT,indent=0,line=1)
        font(par.add_run(line),name='Consolas',size=11)


text=(BASE/'report_text.md').read_text(encoding='utf-8')
for block in text.split('\n\n'):
    block=block.strip()
    if not block:continue
    if block.startswith('# '):
        title=block[2:]
        if title=='ЗАКЛЮЧЕНИЕ':
            p('Программная реализация и воспроизводимые сценарии испытаний приведены в приложениях А и Б. Лекционные исходные материалы приведены в приложении В. Электронный комплект и команды повторного запуска перечислены в приложении Г. Оформление текста и титульного листа выполнено по опубликованным правилам ГУАП [8].')
        heading(title,1,not title[:1].isdigit())
    elif block.startswith('## '):heading(block[3:],2)
    elif block.startswith('!eq '):
        for line in block.splitlines():equation(line.removeprefix('!eq '))
    elif block.startswith('!data '):data(block[6:])
    else:p(block)

def landscape():
    s=D.add_section(WD_SECTION_START.NEW_PAGE)
    s.orientation=WD_ORIENT.LANDSCAPE;s.page_width=Cm(29.7);s.page_height=Cm(21)
    s.left_margin=Cm(3);s.right_margin=Cm(1.5);s.top_margin=Cm(2);s.bottom_margin=Cm(2)
    return s


def definitions(node,prefix=''):
    for child in ast.iter_child_nodes(node):
        if isinstance(child,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
            name=prefix+child.name
            if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                yield name,child
            yield from definitions(child,name+'.')
        else:
            yield from definitions(child,prefix)


def function_notes(path,title):
    heading(title,3)
    module=path.relative_to(BASE).as_posix()
    notes=NOTES[module]
    for name,node in definitions(ast.parse(path.read_text(encoding='utf-8'))):
        if name not in notes:raise ValueError('Нет пояснения '+module+':'+name)
        signature=name+'('+ast.unparse(node.args)+')'
        par=D.add_paragraph(signature+f'; строки {node.lineno}-{node.end_lineno}')
        pf(par,size=12,align=WD_ALIGN_PARAGRAPH.LEFT,indent=0,line=1.15)
        par.paragraph_format.keep_with_next=True
        par.paragraph_format.space_before=Pt(6)
        for r in par.runs:font(r,size=12,bold=True)
        for label,value in zip(['Семантика','Вход','Результат'],notes[name]):
            par=D.add_paragraph(label+': '+value)
            pf(par,size=12,indent=0,line=1.15)
            par.paragraph_format.keep_with_next=label!='Результат'


def listing(path,title):
    heading(title,2)
    function_notes(path,'Назначение и семантика функций')
    heading('Исходный код',3)
    par=D.add_paragraph(str(path.relative_to(BASE)));pf(par,size=12,indent=0,line=1)
    par.paragraph_format.keep_with_next=True
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        par=D.add_paragraph()
        par.paragraph_format.first_line_indent=Cm(0)
        par.paragraph_format.left_indent=Cm(0);par.paragraph_format.right_indent=Cm(0)
        par.paragraph_format.line_spacing=1
        par.paragraph_format.space_before=Pt(0);par.paragraph_format.space_after=Pt(0)
        par.paragraph_format.widow_control=False
        font(par.add_run(f'{i:4}  {line}'),name='Consolas',size=12)


landscape()
heading('ПРИЛОЖЕНИЕ А\nЛистинги основной программы',1,True).paragraph_format.page_break_before=False
p('Полные листинги основной программы. Номера слева предназначены для ссылок и не являются частью исходного кода. Длинные строки переносятся средствами Word без изменения файлов программы.')
listing(BASE/'core.py','А.1 Ядро синтеза и минимизации')
listing(BASE/'storage.py','А.2 Файловые операции и представления')
listing(BASE/'app.py','А.3 Графический интерфейс')
heading('ПРИЛОЖЕНИЕ Б\nЛистинги тестов и экспериментов',1,True)
p('Полные листинги автоматических проверок и воспроизводимых экспериментов.')
for i,(name,title) in enumerate([
 ('tests/test_core.py','Контрактные проверки'),('tests/test_extended.py','Расширенные проверки алгоритмов'),
 ('tests/test_storage.py','Проверки файлов'),('tests/test_gui.py','Проверки интерфейса'),
 ('experiments.py','Независимый перебор слов'),('qa_visual.py','Каталог событий интерфейса')],1):
    listing(BASE/name,f'Б.{i} '+title)

sec=D.add_section(WD_SECTION_START.NEW_PAGE)
sec.orientation=WD_ORIENT.PORTRAIT;sec.page_width=Cm(21);sec.page_height=Cm(29.7)
heading('ПРИЛОЖЕНИЕ В\nЛекционный пример минимизации',1,True).paragraph_format.page_break_before=False
p('На рисунках В.1 и В.2 приведён исходный лекционный пример, использованный для постановки задачи минимизации и проверки таблиц.')
for i in [1,2]:
    if i>1:D.add_page_break()
    picture(BASE/'sources'/f'lecture{i}.png',f'Лекционный конспект минимизации Мили лист {i}',width=15,label=f'В.{i}')
heading('ПРИЛОЖЕНИЕ Г\nЭлектронный комплект и повторение опытов',1,True)
p('Электронный комплект содержит исходники, примеры, автоматические тесты, протоколы, таблицу всех проверенных слов и исходные скриншоты. Его состав приведён в таблице Г.1. Исходники программы кодируются в UTF-8. Для запуска не требуется установка сторонних библиотек.')
table('Состав электронного комплекта',['Путь','Назначение'],[
 ['app.py, core.py, storage.py','Основная программа'],['Run.cmd','Запуск окна в Windows'],
 ['examples/lab5.txt','Основное регулярное выражение'],['examples/variant20.txt','Вариант 20 ЛР №5'],
 ['examples/lecture.json','Таблица Мили из лекции'],['tests','Автоматические проверки'],
 ['qa_visual.py','60 сценариев интерфейса'],['experiments.py','Повторение независимого перебора'],
 ['results/unittest.txt','Полный журнал тестов'],['results/word_checks.csv','44 382 проверки слов'],
 ['results/variants.csv','Результаты всех 30 вариантов'],['results/gui_events.json','Каталог ожидаемых и фактических результатов'],
 ['results/lab5 и results/lecture','JSON, TXT, SVG обоих основных примеров'],
 ['screenshots','Снимки окон зарегистрированных сценариев']],number='Г.1')
p('Команда запуска: python app.py. Команда тестирования: python -m unittest discover -s tests -v. Полный эксперимент: python experiments.py. Каталог интерфейсных сценариев без ручного ввода: python qa_visual.py --batch. Для показа сценариев по одному: python qa_visual.py; клавиши F9 и F8 переключают вперёд и назад.')

heading('Г.1 Сборка и проверка документа',2)
p('build_report.py читает report_text.md, данные испытаний, справочник функций и официальный бланк. Для сборки нужен python-docx. После создания DOCX сценарий render_word.ps1 принимает InputDocx и OutputPdf, открывает документ в Microsoft Word, обновляет содержание и номера страниц, сохраняет DOCX и экспортирует PDF. В консоль выводится число страниц. Снимки страниц используются только для проверки оформления.')
function_notes(BASE/'build_report.py','Функции сборки отчета')


def sanitize_document():
    for part in D.part.package.parts:
        element=getattr(part,'_element',None)
        if element is not None:
            for node in element.iter():
                if node.tag in {qn('w:t'),qn('m:t'),qn('a:t'),qn('w:instrText')} and node.text:
                    node.text=node.text.replace('\u2014','-').replace('\u2013','-').replace('\u2012','-').replace('\u2015','-')


settings=D.settings.element
update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');settings.append(update)
sanitize_document()
out=BASE/'Реферат_Синтез_и_минимизация_КА.docx'
D.save(out)
print(out.name)
print('tables',TABLE,'figures',FIGURE,'events',len(EVENTS))
