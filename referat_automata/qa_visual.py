"""Интеграционные сценарии GUI; F9 — следующий, F8 — предыдущий.

Вызывает реальные обработчики App и проверяет состояние виджетов.
Файловые диалоги изолируются mock: путь/отмена задаются детерминированно.
Снимки настоящего окна снимаются отдельно Computer Use.
"""
import copy
import json
from pathlib import Path
import tkinter as tk
import sys
from unittest.mock import patch
from app import App
import core

BASE=Path(__file__).resolve().parent
QA=BASE/'results/qa_files'; QA.mkdir(exist_ok=True)
(QA/'bad_encoding.txt').write_bytes(b'\xff\xfe\xff')
(QA/'big.txt').write_bytes(b'x'*32_000_001)
(QA/'block').write_text('Это файл, а не папка.',encoding='utf-8')

root=tk.Tk()
panel=tk.Frame(root,bg='#e8eef5',padx=12,pady=7)
panel.pack(side='top',fill='x')
title=tk.StringVar(); expectation=tk.StringVar(); outcome=tk.StringVar()
tk.Label(panel,textvariable=title,font=('Segoe UI',12,'bold'),bg='#e8eef5',anchor='w').pack(fill='x')
tk.Label(panel,textvariable=expectation,font=('Segoe UI',10),bg='#e8eef5',anchor='w').pack(fill='x')
tk.Label(panel,textvariable=outcome,font=('Segoe UI',10),fg='#156c3b',bg='#e8eef5',anchor='w').pack(fill='x')
a=App(root); root.geometry('1220x940')
records=[]; current=-1


def expr(text='a<b|c>d', limit='256'):
    a.limit.set(limit); a.set_source('РВ',text); a.build()


def word(text):
    a.word.set(text); a.check_word()


def tab(name): a.notebook.select(a.frames[name])


def invalid(text, needle, limit='256'):
    expr(text,limit)
    assert a.machine is None and needle in a.status.get(),a.status.get()


def opened(path):
    with patch('app.filedialog.askopenfilename',return_value=str(path)):
        a.open_file()


def exported(path):
    with patch('app.filedialog.askdirectory',return_value=str(path)):
        a.export()


def json_case(data):
    a.set_source('Мили JSON',json.dumps(data,ensure_ascii=False)); a.build()


def base(): expr(); assert len(a.small.states)==4
def accept(): base(); word('ad'); assert 'ДОПУСТИМО' in a.status.get()
def reject(): base(); word('ab'); assert a.status.get()=='ОТКЛОНЕНО'
def extra(): base(); word('add'); assert a.status.get()=='ОТКЛОНЕНО'
def unknown(): base(); word('az'); assert 'не входит' in a.status.get()
def empty_reject(): base(); word(''); assert a.status.get()=='ОТКЛОНЕНО'
def empty_accept(): expr('<a>'); word(''); assert a.status.get()=='ДОПУСТИМО'
def epsilon(): expr('ε'); word(''); assert len(a.small.states)==1 and a.status.get()=='ДОПУСТИМО'
def nested(): expr('(<a><a>|<bε>)'); word('ab'); assert a.status.get()=='ОТКЛОНЕНО'
def unicode(): expr(' a ⟨ b | c ⟩ d '); word('abcd'); assert a.status.get()=='ДОПУСТИМО'
def longword(): base(); word('a'*10001); assert '10000' in a.status.get()
def lecture(): a.example_lecture(); assert len(a.small.states)==3
def lecture_word(): lecture(); word('xyx'); assert core.run(a.machine,'xyx')['outputs']==['1','0','2']
def lecture_empty(): lecture(); word(''); assert 'ВЫХОДНОЕ СЛОВО: ε'==a.status.get()
def json_bad(): a.set_source('Мили JSON','{'); a.build(); assert 'Ошибка JSON' in a.status.get()
def bad_target():
    d=core.lecture_machine().to_dict(); d['transitions']['q1']['x'][0]='ghost'
    json_case(d); assert 'неизвестное' in a.status.get()
def missing():
    d=core.lecture_machine().to_dict(); del d['transitions']['q1']['x']
    json_case(d); assert 'ровно один' in a.status.get()
def unreachable():
    d=core.lecture_machine().to_dict(); d['states'].append('unused')
    d['transitions']['unused']={'x':['unused',9],'y':['unused',9]}
    json_case(d); tab('Разбиения'); assert 'unused' not in a.mapping
def refinement():
    json_case({'states':['s0','s1','s2','s3'],'start':'s0','alphabet':['a'],
      'transitions':{'s0':{'a':['s1',0]},'s1':{'a':['s2',0]},'s2':{'a':['s3',0]},'s3':{'a':['s3',1]}}})
    tab('Разбиения'); assert [len(p) for p in a.partitions]==[2,3,4,4]
def load_txt(): opened(BASE/'examples/lab5.txt'); a.build(); assert a.machine.recognizer
def load_json(): opened(BASE/'examples/lecture.json'); a.build(); assert len(a.small.states)==3
def cancel_open(): base(); old=a.machine; opened(''); assert a.machine is old; tab('События')
def file_missing(): opened(QA/'missing.txt'); assert 'Не удалось прочитать' in a.status.get(); tab('События')
def encoding(): opened(QA/'bad_encoding.txt'); assert 'Не удалось прочитать' in a.status.get(); tab('События')
def bigfile(): opened(QA/'big.txt'); assert '32 МБ' in a.status.get(); tab('События')
def save():
    base(); exported(QA/'exported')
    assert len(list((QA/'exported').glob('*')))==5; tab('События')
def cancel_export(): base(); old=a.machine; exported(''); assert a.machine is old; tab('События')
def save_error(): base(); exported(QA/'block'); assert 'Не удалось сохранить' in a.status.get(); tab('События')
def clear(): a.clear(); assert a.machine is None and not a.source.get('1.0','end-1c')
def before_build(): a.clear(); a.check_word(); assert a.status.get()=='Сначала постройте автомат.'
def recovery(): invalid('a|','Пустая'); base(); assert a.status.get().startswith('Готово')
def edit():
    base(); a.source.insert('end','a'); root.update(); assert a.machine is None
def help_page(): tab('Справка'); assert 'ЛИМИТЫ' in a.outputs['Справка'].get('1.0','end')
def places(): base(); tab('Места')
def partitions(): base(); tab('Разбиения')
def before_graph(): base(); a.draw(a.machine); tab('Графы')
def after_graph(): lecture(); a.draw(a.small); tab('Графы')
def one(): expr('<a>'); assert len(a.small.states)==1


CASES=[
('Проверка до построения','Сообщение «Сначала постройте автомат»',before_build),
('Синтез по ЛР5','6 исходных, 4 минимальных состояния; эквивалентность',base),
('Места и распространение индексов','Таблица подчинения и сырые подмножества',places),
('Разбиения распознавателя','Устойчивые классы и точная эквивалентность',partitions),
('Исходный граф','Граф шести состояний, включая отказ',before_graph),
('Минимальный граф лекции','Граф трёх классов Мили',after_graph),
('Допустимое слово ad','Допустимо; выходы 0, 1',accept),
('Незавершённое слово ab','Отклонено; выходы 0, 0',reject),
('Продолжение принятого слова add','Отклонено после последнего символа',extra),
('Символ вне алфавита az','Ошибка на второй позиции',unknown),
('Пустое слово для a<b|c>d','Отклонено; ноль переходов',empty_reject),
('Пустое слово для <a>','Допустимо; ноль выходных сигналов',empty_accept),
('Выражение ε','Единственное конечное состояние; пустое слово принято',epsilon),
('Вложенность и альтернатива','(<a><a>|<bε>) отклоняет ab',nested),
('Типографские скобки и пробелы','a⟨b|c⟩d принимает abcd',unicode),
('Незакрытая скобка','Ошибка с позицией; результат сброшен',lambda:invalid('(a','Ожидалась')),
('Пустая альтернатива','Ошибка пустой ветви',lambda:invalid('a|','Пустая')),
('Неподдерживаемая операция','a* отклоняется как неверное РВ',lambda:invalid('a*','Недопустимый')),
('Лимит длины выражения','301 знак: отказ до синтеза',lambda:invalid('a'*301,'300')),
('Лимит вложенности','41 уровень: сообщение о лимите 40',lambda:invalid('('*41+'a'+')'*41,'40')),
('Нечисловой лимит состояний','Сообщение о целом числе',lambda:invalid('ab','целым','abc')),
('Превышение числа состояний','ab с лимитом 1: контролируемый отказ',lambda:invalid('ab','Превышен','1')),
('Лимит длины слова','10001 знак: сообщение о лимите 10000',longword),
('Лекционный пример минимизации','5 состояний → 3 класса',lecture),
('Выходы лекционного автомата','xyx даёт 1, 0, 2 до и после минимизации',lecture_word),
('Пустой вход автомата Мили','Выходное слово ε без классификации допустимости',lecture_empty),
('Синтаксическая ошибка JSON','Номер строки и столбца ошибки',json_bad),
('Неизвестная цель перехода JSON','Ошибка неизвестного состояния',bad_target),
('Неполный автомат JSON','Требование перехода на каждый вход',missing),
('Недостижимое состояние','unused удалено; результат содержит 3 класса',unreachable),
('Несколько уточнений','Число классов 2 → 3 → 4 → 4',refinement),
('Одноклассовый минимальный автомат','<a>: 2 исходных состояния объединены в 1 класс',one),
('Чтение TXT','Выражение прочитано и построено',load_txt),
('Чтение JSON','Лекционный автомат прочитан и минимизирован',load_json),
('Отмена открытия','Текущий автомат сохранён',cancel_open),
('Отсутствующий файл','Диагностика чтения; окно продолжает работу',file_missing),
('Неверная кодировка','Диагностика UTF-8',encoding),
('Слишком большой файл','Файл больше 32 МБ отклонён',bigfile),
('Экспорт комплекта','Созданы JSON ×2, SVG ×2 и протокол TXT',save),
('Отмена экспорта','Текущий результат сохранён',cancel_export),
('Ошибка сохранения','Путь является файлом; вывод диагностики',save_error),
('Очистка','Данные и результаты сброшены',clear),
('Восстановление после ошибки','После неверного РВ повторное построение успешно',recovery),
('Изменение входа','Старый автомат сброшен до нового построения',edit),
('Встроенная справка','Синтаксис, алгоритмы, лимиты и операции доступны',help_page),
('Пустое регулярное выражение','Сообщение о необходимости ввода',lambda:invalid('','Введите')),
('Лимит вне диапазона','Число 513 отклонено; допустимо 1…512',lambda:invalid('a','512','513')),
('Слишком длинное число JSON','5000 цифр: контролируемая ошибка парсера',lambda:json_resource('1'*5000)),
('Чрезмерно вложенный JSON','10000 скобок: контролируемая ошибка парсера',lambda:json_resource('['*10000+'0'+']'*10000)),
('Неверный корень JSON','Список вместо объекта автомата отклонён',lambda:json_invalid([], 'объект')),
('Повтор имён состояний','Дубли states отклонены',lambda:json_invalid(dict(core.lecture_machine().to_dict(),states=['q1','q1']),'повторяющиеся')),
('Многосимвольный вход JSON','Вход xx отклонён',lambda:json_invalid(dict(core.lecture_machine().to_dict(),alphabet=['xx']),'одним')),
('Неизвестное начальное состояние','start=ghost отклонено',lambda:json_invalid(dict(core.lecture_machine().to_dict(),start='ghost'),'Начальное')),
('Неверный тип recognizer','Строка вместо bool отклонена',lambda:json_invalid(dict(core.lecture_machine().to_dict(),recognizer='true'),'true или false')),
('Неизвестное конечное состояние','finals=[ghost] отклонено',lambda:json_invalid(dict(core.lecture_machine().to_dict(),finals=['ghost']),'finals')),
('Пустые скобки','() отклоняется; используйте ε',lambda:invalid('()','Пустая')),
('Лишняя закрывающая скобка','a) отклоняется с позицией',lambda:invalid('a)','Лишняя')),
('Проверка границы длины слова','10000 букв a допустимы для <a>',lambda:boundary_word()),
('Повторное построение','Повторное построение даёт тот же автомат',lambda:repeat_build()),
('Экспорт до построения','Сообщение «Сначала постройте автомат»',lambda:export_before())]


def json_resource(text):
    a.set_source('Мили JSON',text); a.build()
    assert a.machine is None and 'Ошибка JSON' in a.status.get()


def json_invalid(data,needle):
    json_case(data); assert a.machine is None and needle in a.status.get()


def boundary_word():
    expr('<a>'); a.word.set('a'*10000)
    result=core.run(a.machine,a.word.get())
    assert result['accepted'] and len(result['trace'])==10000
    # Реальный GUI-обработчик, текст прокручивается; не подменяем результат.
    a.check_word(); assert a.status.get()=='ДОПУСТИМО'


def repeat_build():
    base(); old=a.machine.to_dict(); a.build(); assert a.machine.to_dict()==old


def export_before():
    a.clear(); a.export(); assert a.status.get()=='Сначала постройте автомат.'


def show(index):
    global current
    if not 0<=index<len(CASES): return
    current=index; name, expected, action=CASES[index]
    a.write(a.outputs['События'],'')
    a.limit.set('256')
    error=None
    try: action()
    except Exception as exc: error=f'{type(exc).__name__}: {exc}'
    code=f'E{index+1:02d}'
    record={'id':code,'name':name,'expected':expected,
            'actual':a.status.get(),'passed':error is None,'error':error,
            'screenshot':f'{code}.png'}
    records[:]=[r for r in records if r['id']!=code]+[record]
    records.sort(key=lambda r:r['id'])
    (BASE/'results/gui_events.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    title.set(f'{code}  {name}   |   F9 — следующий сценарий   ({index+1}/{len(CASES)})')
    expectation.set('Ожидается: '+expected)
    outcome.set(('ПРОЙДЕНО: ' if error is None else 'ОШИБКА ТЕСТА: ')+(error or a.status.get()))
    root.title(f'Проверка GUI {code} — конечные автоматы')
    root.update_idletasks()


if '--batch' in sys.argv:
    root.withdraw()
    for number in range(len(CASES)):
        show(number)
    root.destroy()
    sys.exit(0 if all(r['passed'] for r in records) else 1)
elif '--controlled' in sys.argv:
    request_file=BASE/'results/qa_request.txt'
    request_file.write_text('0',encoding='ascii')
    def poll():
        try:
            requested=int(request_file.read_text(encoding='ascii'))
            if requested!=current: show(requested)
        except (ValueError,OSError): pass
        root.after(150,poll)
    root.after(150,poll)
elif '--auto' in sys.argv:
    def advance():
        if current+1<len(CASES):
            show(current+1)
            root.after(2400,advance)
    root.after(5000,advance)
else:
    root.bind('<F9>',lambda e:show(current+1))
    root.bind('<F8>',lambda e:show(current-1))
show(0)
root.mainloop()
