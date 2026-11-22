"""Автономный оконный практикум: Python и стандартный Tkinter."""
import json
import math
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from core import InputError, synthesize, from_dict, lecture_machine, minimize, compare, run
from storage import load_input, export_bundle, transition_text, matrix_text, table, graph_layout

HELP = '''СИНТЕЗ ПО МЕСТАМ И МИНИМИЗАЦИЯ МИЛИ

РВ: a, b, A, 0 — отдельные входные символы; ab — конкатенация;
a|b — выбор; (ab) — группировка; <ab> или ⟨ab⟩ — 0 и более повторений.
Расширение ε задаёт пустое слово. Пробелы в РВ игнорируются.
Символы *, +, ?, [], экранирование и диапазоны не поддерживаются.

1. Введите РВ или выберите «Пример ЛР5». Нажмите «Построить».
2. Изучите таблицы, графы, места и последовательность разбиений.
3. На вкладке «Проверка слова» введите слово и нажмите «Проверить».
   Пустое поле — пустое слово. Пробелы в слове не удаляются.
4. «Открыть» читает UTF-8 TXT с РВ либо JSON с автоматом Мили.
5. «Экспорт» сохраняет JSON, протокол и два SVG в выбранную папку.
   Имена original.json, minimal.json, protocol.txt, original.svg,
   minimal.svg используются повторно при следующем экспорте туда же.

РЕЖИМ МИЛИ JSON
Воспользуйтесь «Пример лекции» и измените таблицу в JSON.
states — список состояний; alphabet — односимвольные входы;
start — начальное состояние; transitions[q][x] = [цель, выход].
Нужен полный детерминированный автомат. Выходы — строки или целые.
В этом режиме нет принимающих состояний: результат — выходное слово.

КОНТРОЛЬ КОРРЕКТНОСТИ
Синтез: индексы → подчинение → замыкание → достижимые подмножества.
Пустое множество {} — состояние отказа с петлями на всех входах.
Выход 1 означает, что прочитанный префикс допустим; ответ для всего
слова определяется после чтения всех символов. Для ε проверяется
конечность начального состояния, выходных сигналов нет.
Минимизация: удаление недостижимых; группировка по выходам;
уточнение по классам целей до устойчивости. Для распознавателя
дополнительно сохраняется конечность. Проверяются все достижимые
пары исходного и минимального автоматов, включая выходы.

ЛИМИТЫ
РВ: 300 знаков, вложенность 40, по умолчанию 256 состояний
(изменяемый предел 1…512). JSON: 512 состояний и 62 входа;
файл до 32 МБ; слово до 10000 знаков. Графы свыше 40 состояний
смотрите в экспортированных SVG; таблицы доступны с прокруткой.

СОБЫТИЯ
Ошибки выводятся в строку состояния и журнал, окно не закрывается.
При изменении входа старый результат сбрасывается; повторите сборку.
Отмена файлового диалога сохраняет текущий результат.
'''


class App:
    def __init__(self, root):
        self.root = root
        root.title('Конечные автоматы — синтез и минимизация')
        root.geometry('1220x850')
        root.minsize(960,700)
        style=ttk.Style(root)
        style.theme_use('clam')
        style.configure('.',font=('Segoe UI',11))
        style.configure('TButton',padding=(10,6))
        style.configure('TNotebook.Tab',padding=(12,7))
        self.machine=self.small=None
        self.partitions=[]; self.mapping={}
        self.mode=tk.StringVar(value='РВ'); self.word=tk.StringVar()
        self.limit=tk.StringVar(value='256'); self.status=tk.StringVar(value='Готово. Выберите пример или введите выражение.')
        self.summary=tk.StringVar(value='Синтез по ЛР №5  ·  Минимизация Мили по лекции')
        self._setting=False
        header=tk.Frame(root,bg='#172d48',padx=20,pady=12)
        header.pack(fill='x')
        tk.Label(header,text='СИНТЕЗ И МИНИМИЗАЦИЯ',font=('Segoe UI',18,'bold'),bg='#172d48',fg='white').pack(anchor='w')
        tk.Label(header,textvariable=self.summary,font=('Segoe UI',11),bg='#172d48',fg='#d8e9fb').pack(anchor='w')
        bar=ttk.Frame(root,padding=(12,8)); bar.pack(fill='x')
        ttk.Label(bar,text='Вход:').pack(side='left')
        self.mode_box=ttk.Combobox(bar,textvariable=self.mode,values=['РВ','Мили JSON'],state='readonly',width=12)
        self.mode_box.pack(side='left',padx=6)
        self.mode_box.bind('<<ComboboxSelected>>',lambda e:self.invalidate())
        for label,cmd in [('Пример ЛР5',self.example_regex),('Пример лекции',self.example_lecture),
                          ('Открыть',self.open_file),('Очистить',self.clear)]:
            ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=3)
        ttk.Label(bar,text='Лимит:').pack(side='left',padx=(10,3))
        ttk.Entry(bar,textvariable=self.limit,width=6).pack(side='left')
        ttk.Button(bar,text='Построить',command=self.build).pack(side='right',padx=3)
        self.source=tk.Text(root,height=4,wrap='word',font=('Consolas',12),undo=True,padx=10,pady=6)
        self.source.pack(fill='x',padx=12)
        self.source.bind('<<Modified>>',self.modified)
        self.notebook=ttk.Notebook(root); self.notebook.pack(fill='both',expand=True,padx=12,pady=8)
        self.outputs={}; self.frames={}
        for name in ['Автоматы','Графы','Места','Разбиения','Проверка слова','События','Справка']:
            frame=ttk.Frame(self.notebook); self.frames[name]=frame
            self.notebook.add(frame,text=name)
            if name not in ['Графы','Проверка слова']:
                self.outputs[name]=self.text_area(frame)
        graphbar=ttk.Frame(self.frames['Графы']); graphbar.pack(fill='x')
        ttk.Button(graphbar,text='Исходный граф',command=lambda:self.draw(self.machine)).pack(side='left')
        ttk.Button(graphbar,text='Минимальный граф',command=lambda:self.draw(self.small)).pack(side='left')
        graphframe=ttk.Frame(self.frames['Графы']); graphframe.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(graphframe,bg='white',highlightthickness=0)
        sx=ttk.Scrollbar(graphframe,orient='horizontal',command=self.canvas.xview)
        sy=ttk.Scrollbar(graphframe,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
        sx.pack(side='bottom',fill='x'); sy.pack(side='right',fill='y'); self.canvas.pack(fill='both',expand=True)
        wordbar=ttk.Frame(self.frames['Проверка слова'],padding=8); wordbar.pack(fill='x')
        ttk.Label(wordbar,text='Слово (пустое поле = ε):').pack(side='left')
        ttk.Entry(wordbar,textvariable=self.word,width=40).pack(side='left',padx=8)
        self.check_button=ttk.Button(wordbar,text='Проверить',command=self.check_word)
        self.check_button.pack(side='left')
        self.word_output=self.text_area(self.frames['Проверка слова'])
        self.write(self.outputs['Справка'],HELP)
        footer=ttk.Frame(root,padding=(12,4)); footer.pack(side='bottom',fill='x',before=self.notebook)
        self.export_button=ttk.Button(footer,text='Экспорт комплекта',command=self.export)
        self.export_button.pack(side='right')
        ttk.Label(footer,textvariable=self.status,wraplength=950).pack(side='left',fill='x',expand=True)
        self.set_source('РВ','a<b|c>d')

    def text_area(self,frame):
        pane=ttk.Frame(frame); pane.pack(fill='both',expand=True)
        text=tk.Text(pane,height=12,wrap='none',font=('Consolas',12),padx=12,pady=10,state='disabled')
        sx=ttk.Scrollbar(pane,orient='horizontal',command=text.xview)
        sy=ttk.Scrollbar(pane,orient='vertical',command=text.yview)
        text.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
        sx.pack(side='bottom',fill='x'); sy.pack(side='right',fill='y'); text.pack(fill='both',expand=True)
        return text

    @staticmethod
    def write(widget,text):
        widget.configure(state='normal'); widget.delete('1.0','end')
        widget.insert('1.0',text); widget.configure(state='disabled')

    def note(self,text):
        self.status.set(text)
        log=self.outputs['События']; log.configure(state='normal')
        log.insert('end',text+'\n'); log.see('end'); log.configure(state='disabled')

    def invalidate(self):
        self.machine=self.small=None; self.partitions=[]; self.mapping={}
        for name in ['Автоматы','Места','Разбиения']:
            self.write(self.outputs[name],'Введите данные и нажмите «Построить».')
        self.write(self.word_output,'Сначала постройте автомат.')
        self.canvas.delete('all')
        self.summary.set('Вход изменён — требуется построение')

    def modified(self,event=None):
        if self.source.edit_modified():
            self.source.edit_modified(False)
            if not self._setting:
                self.invalidate()
                self.status.set('Вход изменён. Нажмите «Построить».')

    def set_source(self,mode,text):
        self._setting=True
        self.mode.set(mode); self.source.delete('1.0','end'); self.source.insert('1.0',text)
        self.source.edit_modified(False); self.invalidate(); self._setting=False

    def clear(self):
        self.set_source('РВ',''); self.word.set(''); self.note('Поля очищены. Результат сброшен.')

    def example_regex(self):
        self.set_source('РВ','a<b|c>d'); self.build()

    def example_lecture(self):
        self.set_source('Мили JSON',json.dumps(lecture_machine().to_dict(),ensure_ascii=False))
        self.build()

    def build(self):
        source=self.source.get('1.0','end-1c')
        self.invalidate()
        try:
            if self.mode.get()=='РВ':
                try: limit=int(self.limit.get())
                except ValueError: raise InputError('Лимит состояний должен быть целым числом.')
                m=synthesize(source,limit)
            else:
                try: data=json.loads(source)
                except json.JSONDecodeError as error:
                    raise InputError(f'Ошибка JSON: строка {error.lineno}, столбец {error.colno}.')
                except (ValueError, RecursionError):
                    raise InputError('Ошибка JSON: превышен предел вложенности или длины числа.')
                m=from_dict(data)
            small,partitions,mapping=minimize(m)
            verdict=compare(m,small)
            if not verdict['equivalent']:
                raise InputError('Нарушена эквивалентность: '+str(verdict))
            self.machine,self.small=m,small
            self.partitions,self.mapping=partitions,mapping
            info=f'{len(m.states)} → {len(small.states)} состояний; эквивалентность подтверждена ({verdict["pairs"]} пар)'
            self.summary.set(info)
            self.write(self.outputs['Автоматы'],
                'ИСХОДНЫЙ АВТОМАТ   (цель/выход; → начало, * конечность)\n\n'+transition_text(m)+
                '\n\nМИНИМАЛЬНЫЙ АВТОМАТ\n\n'+transition_text(small)+
                '\n\nАВТОМАТНАЯ МАТРИЦА МИНИМАЛЬНОГО АВТОМАТА\n\n'+matrix_text(small))
            rows=[[p['place'],p['before'],p['after'],str(p['main']) if p['main'] is not None else '—',
                   str(p['indices']),str(p['subordinates'])] for p in m.details.get('places',[])]
            self.write(self.outputs['Места'],
                'Место p подчиняет все места последнего столбца (включая себя).\n'+
                'Индексы распространяются от основного места к подчинённым.\n\n'+
                (table(['p','до','после','осн.','все индексы','подчинённые'],rows)+
                 '\n\nСырые состояния:\n'+json.dumps(m.details['subsets'],ensure_ascii=False,indent=2)
                 if rows else 'Режим Мили: места регулярного выражения не используются.'))
            lines=['P0 — группировка по векторам выходов'+(' и конечности.' if m.recognizer else '.'),
                   'Следующий шаг уточняет классы по переходам.\n']
            for i,blocks in enumerate(partitions):
                lines.append(f'P{i}: '+' | '.join('{'+', '.join(block)+'}' for block in blocks))
            lines+=['\nПоследнее разбиение устойчиво.','\nСоответствие: '+str(mapping),
                    '\nНедостижимые удалены: '+str([q for q in m.states if q not in mapping]),
                    '\nТочная проверка: '+verdict['reason'],f'Проверено пар: {verdict["pairs"]}']
            self.write(self.outputs['Разбиения'],'\n'.join(lines))
            self.draw(small); self.notebook.select(self.frames['Автоматы'])
            self.note('Готово: '+info)
        except InputError as error:
            self.note('Ошибка: '+str(error))

    def check_word(self):
        if self.machine is None:
            self.note('Сначала постройте автомат.'); return
        try:
            result=run(self.machine,self.word.get()); second=run(self.small,self.word.get())
            if result['error']:
                title='ОШИБКА ВХОДНОГО СЛОВА: '+result['error']
            elif self.machine.recognizer:
                title='ДОПУСТИМО' if result['accepted'] else 'ОТКЛОНЕНО'
            else:
                title='ВЫХОДНОЕ СЛОВО: '+(', '.join(result['outputs']) or 'ε')
            text=f'Слово: {self.word.get() or "ε"}\nРезультат: {title}\n\n'
            for name,r in [('ИСХОДНЫЙ АВТОМАТ',result),('МИНИМАЛЬНЫЙ АВТОМАТ',second)]:
                text+=name+'\n'+table(['Шаг','Из','Вход','В','Выход'],r['trace'])+'\n'
                text+=f'Итоговое состояние: {r["state"]}; выходы: '+(', '.join(r['outputs']) or 'ε')+'\n\n'
            text+='Результаты совпадают: '+str(result['outputs']==second['outputs'] and result['accepted']==second['accepted'])
            self.write(self.word_output,text); self.notebook.select(self.frames['Проверка слова'])
            self.note(title)
        except InputError as error:
            self.write(self.word_output,'Ошибка: '+str(error)); self.note('Ошибка: '+str(error))

    def open_file(self):
        path=filedialog.askopenfilename(title='Открыть РВ или автомат Мили',
            filetypes=[('Входные файлы','*.txt *.json'),('Все файлы','*.*')])
        if not path:
            self.note('Открытие отменено.'); return
        try:
            mode,text=load_input(path); self.set_source(mode,text)
            self.note('Открыт файл: '+Path(path).name+'; нажмите «Построить».')
        except InputError as error: self.note('Ошибка: '+str(error))

    def export(self):
        if self.machine is None:
            self.note('Сначала постройте автомат.'); return
        folder=filedialog.askdirectory(title='Папка для комплекта (5 файлов)')
        if not folder:
            self.note('Экспорт отменён.'); return
        try:
            files=export_bundle(folder,self.machine,self.small,self.partitions,self.mapping)
            self.note(f'Сохранено {len(files)} файлов: {folder}')
        except InputError as error: self.note('Ошибка: '+str(error))

    def draw(self,m):
        c=self.canvas; c.delete('all')
        if m is None: return
        if len(m.states)>40:
            c.create_text(25,25,text='Граф содержит больше 40 состояний. Используйте экспорт SVG.',anchor='nw')
            return
        positions,size=graph_layout(m)
        c.configure(scrollregion=(0,0,max(size,900),max(size,420)))
        c.xview_moveto(0); c.yview_moveto(0)
        for q in m.states:
            grouped={}
            for x,(t,out) in m.transitions[q].items(): grouped.setdefault(t,[]).append(f'{x}/{out}')
            x1,y1=positions[q]
            for t,labels in grouped.items():
                x2,y2=positions[t]
                if q==t:
                    c.create_line(x1-16,y1-20,x1-45,y1-70,x1+45,y1-70,x1+16,y1-20,
                                  smooth=True,arrow='last',fill='#475569',width=1.5)
                    lx,ly=x1,y1-65
                else:
                    dx,dy=x2-x1,y2-y1; norm=math.hypot(dx,dy)
                    cx,cy=(x1+x2)/2-dy*.16,(y1+y2)/2+dx*.16
                    c.create_line(x1+dx*28/norm,y1+dy*28/norm,cx,cy,
                                  x2-dx*30/norm,y2-dy*30/norm,smooth=True,arrow='last',fill='#475569',width=1.5)
                    lx,ly=(x1+x2+2*cx)/4,(y1+y2+2*cy)/4-10
                c.create_text(lx,ly,text=', '.join(labels),font=('Segoe UI',11),fill='#1e40af')
        for q,(x,y) in positions.items():
            c.create_oval(x-26,y-26,x+26,y+26,fill='#e0f2fe',outline='#334155',width=1.5)
            if q in m.finals: c.create_oval(x-22,y-22,x+22,y+22,outline='#334155')
            if q==m.start: c.create_line(x-65,y,x-28,y,arrow='last',width=1.5)
            c.create_text(x,y,text=q,font=('Segoe UI',12,'bold'))


if __name__=='__main__':
    window=tk.Tk(); App(window); window.mainloop()
