"""Воспроизводимые измерения, полный журнал слов и результаты unittest."""
import csv
import io
import itertools
import json
from pathlib import Path
import random
import re
import time
import unittest
import core
from storage import export_bundle

BASE=Path(__file__).resolve().parent


def execute():
    out=BASE/'results'; out.mkdir(exist_ok=True)
    import sys
    sys.path.insert(0,str(BASE/'tests'))
    from test_extended import VARIANTS, oracle, words
    suite=unittest.defaultTestLoader.discover(str(BASE/'tests'))
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (out/'unittest.txt').write_text(stream.getvalue(),encoding='utf-8')
    rows=[]; total=0; mismatches=0
    with (out/'word_checks.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.writer(file)
        writer.writerow(['corpus','case','expression','word','expected','actual','prefix_outputs'])
        def check(kind,num,expr,length,alphabet=None):
            nonlocal total,mismatches
            started=time.perf_counter_ns(); m=core.synthesize(expr)
            small,parts,mapping=core.minimize(m)
            elapsed=(time.perf_counter_ns()-started)/1_000_000
            verdict=core.compare(m,small)
            assert verdict['equivalent']
            count=0
            for word in words(alphabet or m.alphabet,length):
                expected=re.fullmatch(oracle(expr),word) is not None
                r=core.run(m,word)
                expected_out=['1' if re.fullmatch(oracle(expr),word[:i]) else '0' for i in range(1,len(word)+1)]
                # Неизвестные символы сравниваются как отказ; префиксные выходы
                # сравниваются только для слова во входном алфавите автомата.
                in_alphabet=all(c in m.alphabet for c in word)
                ok=r['accepted']==expected and (not in_alphabet or r['outputs']==expected_out)
                mismatches+=not ok; total+=1; count+=1
                writer.writerow([kind,num,expr,word,int(expected),int(r['accepted']),','.join(r['outputs'])])
                assert ok,(kind,num,expr,word)
            return {'variant':num,'expression':expr,'alphabet':len(m.alphabet),'states':len(m.states),
                    'minimal':len(small.states),'checks':count,'pairs':verdict['pairs'],
                    'refinements':len(parts)-1,'elapsed_ms':round(elapsed,4)}
        for number,expr in enumerate(VARIANTS,1):
            rows.append(check('ЛР5',number,expr,4))
        rng=random.Random(4332)
        def gen(depth):
            if not depth: return rng.choice(['a','b','ε'])
            mode=rng.randrange(4)
            if mode==0:return '<'+gen(depth-1)+'>'
            if mode==1:return '('+gen(depth-1)+'|'+gen(depth-1)+')'
            return gen(depth-1)+gen(depth-1)
        generated=[]
        for i in range(120):
            expr=gen(3); check('Генератор',i+1,expr,5,'ab'); generated.append(expr)
    for name,m in [('lab5',core.synthesize('a<b|c>d')),('lecture',core.lecture_machine())]:
        small,parts,mapping=core.minimize(m)
        export_bundle(out/name,m,small,parts,mapping)
    summary={'unittest_count':result.testsRun,'unittest_passed':result.wasSuccessful(),
             'word_checks':total,'mismatches':mismatches,'variants':rows,
             'generated_expressions':generated,'seed':4332}
    (out/'experiments.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'variants.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['variants','generated_expressions']}))
    return summary


if __name__=='__main__': execute()
