import copy
import itertools
import random
import re
import unittest
import string
import core

VARIANTS = [
 '<a>(b|c)<d>', 'a<(b|c)>d', '<(a|b)>c<d|e>', 'a<(b|c)|d>e',
 '<a>(b|c)<d|e>', 'a<b>(c|d)<e>', '<(a|b)|c>d<e>', 'a<b><(c|d)>e',
 '<(a|b)><(c|d)>e', 'a<(b|c)><d>e', '<a>b<c>(d|e)', 'a<(b|c)|d><e>',
 '<(a|b)><c>d<e>', 'a<b><(c|d)|e>', '<(a|b)|c><d>e', 'a<(b|c)>d<e|f>',
 '<(a|b)>c<d><e>', 'a<(b|c)|d><e|f>', '<a><(b|c)>d<e>', 'a<b><(c|d)><e>',
 '<(a|b)|c><d|e>f', 'a<(b|c)><(d|e)|f>', '<(a|b)><c><d|e>f',
 'a<(b|c)|d><e><f>', '<(a|b)|c>d<e|f|g>', 'a<(b|c)><d><e|f>',
 '<(a|b)><(c|d)|e><f>', 'a<(b|c)|d>e<f|g>',
 '<(a|b)|c><d|e><f|g>', 'a<(b|c)><(d|e)|f><g>']


def oracle(expr):
    return expr.replace('<', '(?:').replace('>', ')*').replace('ε', '')


def words(alphabet, length):
    for n in range(length+1):
        for xs in itertools.product(alphabet, repeat=n):
            yield ''.join(xs)


class SynthesisTests(unittest.TestCase):
    def test_all_supported_symbols_round_trip(self):
        m=core.synthesize(string.ascii_letters+string.digits)
        self.assertTrue(core.compare(m,core.from_dict(m.to_dict()))['equivalent'])

    def test_state_limit_matches_import_contract(self):
        with self.assertRaises(core.InputError):
            core.synthesize('a',max_states=513)

    def test_all_30_variants_exhaustively_to_length_4(self):
        checked = 0
        for i, expr in enumerate(VARIANTS, 1):
            m = core.synthesize(expr)
            small, _, _ = core.minimize(m)
            self.assertTrue(core.compare(m, small)['equivalent'], i)
            for word in words(m.alphabet, 4):
                checked += 1
                self.assertEqual(core.run(m, word)['accepted'],
                                 re.fullmatch(oracle(expr), word) is not None,
                                 (i, expr, word))
        self.assertGreater(checked, 10000)

    def test_generated_nested_expressions(self):
        rng = random.Random(4332)
        def gen(depth):
            if not depth:
                return rng.choice(['a', 'b', 'ε'])
            mode = rng.randrange(4)
            if mode == 0:
                return '<' + gen(depth-1) + '>'
            if mode == 1:
                return '(' + gen(depth-1) + '|' + gen(depth-1) + ')'
            return gen(depth-1) + gen(depth-1)
        for _ in range(120):
            expr = gen(3)
            m = core.synthesize(expr)
            for word in words('ab', 5):
                self.assertEqual(core.run(m, word)['accepted'],
                                 re.fullmatch(oracle(expr), word) is not None,
                                 (expr, word))
            self.assertTrue(core.compare(m, core.minimize(m)[0])['equivalent'])

    def test_empty_word_and_repeated_identical_letters(self):
        for expr in ['ε', '<a>', '<ε>', '(ε|a)', 'a|aa', '(ab|ac)', '<<a>b>', '<(a|b)>abb']:
            m = core.synthesize(expr)
            for word in words('ab', 6):
                self.assertEqual(core.run(m, word)['accepted'],
                                 re.fullmatch(oracle(expr), word) is not None, (expr, word))

    def test_unicode_brackets_and_whitespace(self):
        self.assertTrue(core.run(core.synthesize(' a ⟨ b | c ⟩ d '), 'ad')['accepted'])

    def test_each_invalid_expression(self):
        for expr in ['', ' ', '()', '<>', 'a|', '|a', '(a', '<a)', 'a)', 'a**', 'a+b', '(a||b)', 'a'*301, '('*41+'a'+')'*41]:
            with self.subTest(expr=expr):
                with self.assertRaises(core.InputError):
                    core.synthesize(expr)

    def test_resource_limits(self):
        with self.assertRaises(core.InputError):
            core.synthesize('ab', max_states=1)
        with self.assertRaises(core.InputError):
            core.synthesize('a', max_states=True)
        with self.assertRaises(core.InputError):
            core.run(core.synthesize('a'), 'a'*10001)

    def test_unknown_symbol_and_empty_sink(self):
        m = core.synthesize('ab')
        self.assertIsNotNone(core.run(m, 'az')['error'])
        self.assertFalse(core.run(m, 'aba')['accepted'])
        self.assertIn([], m.details['subsets'].values())
        sink = next(q for q, s in m.details['subsets'].items() if not s)
        self.assertTrue(all(target == sink for target, _ in m.transitions[sink].values()))

    def test_index_propagation(self):
        m = core.synthesize('a<b|c>d')
        self.assertEqual(m.details['subsets']['q0'], [0])
        # После a сырой алгоритм хранит {1}, а не уже объединённый класс {1,2,3}.
        q = m.transitions['q0']['a'][0]
        self.assertEqual(m.details['subsets'][q], [1])
        after_cycle = m.details['places'][6]
        self.assertEqual(after_cycle['indices'], [1,2,3])


class MinimizationTests(unittest.TestCase):
    def test_unreachable_removed_and_single_state(self):
        m = core.lecture_machine()
        m.states.append('unused')
        m.transitions['unused'] = {'x':['unused','9'], 'y':['unused','9']}
        small, _, mapping = core.minimize(m)
        self.assertNotIn('unused', mapping)
        self.assertEqual(len(small.states), 3)
        one = core.synthesize('<a>')
        self.assertEqual(len(core.minimize(one)[0].states), 1)

    def test_multiple_refinement_rounds(self):
        m = core.from_dict({'states':['s0','s1','s2','s3'], 'start':'s0', 'alphabet':['a'],
          'transitions':{'s0':{'a':['s1',0]},'s1':{'a':['s2',0]},
                         's2':{'a':['s3',0]},'s3':{'a':['s3',1]}}})
        small, history, _ = core.minimize(m)
        self.assertEqual([len(p) for p in history], [2,3,4,4])
        self.assertEqual(len(small.states), 4)

    def test_output_difference_witness_and_final_difference(self):
        a = core.lecture_machine()
        b = copy.deepcopy(a)
        b.transitions['q3']['x'][1] = '9'
        verdict = core.compare(a,b)
        self.assertFalse(verdict['equivalent'])
        self.assertEqual(verdict['witness'], 'yx')
        self.assertNotEqual(core.run(a,'yx')['outputs'], core.run(b,'yx')['outputs'])
        a = core.synthesize('ε')
        b = copy.deepcopy(a)
        b.finals.clear()
        self.assertEqual(core.compare(a,b)['witness'], '')

    def test_mealy_empty_word_has_no_output(self):
        self.assertEqual(core.run(core.lecture_machine(), '')['outputs'], [])
        self.assertIsNone(core.run(core.lecture_machine(), '')['accepted'])

    def test_minimization_idempotent(self):
        for expr in VARIANTS:
            a = core.minimize(core.synthesize(expr))[0]
            b = core.minimize(a)[0]
            self.assertEqual(len(a.states),len(b.states))
            self.assertTrue(core.compare(a,b)['equivalent'])

    def test_bad_json_schema_events(self):
        good = core.lecture_machine().to_dict()
        mutations = [None, [], {}, {'states': 'q'},
                     dict(good, alphabet=['xx']), dict(good, start='missing'),
                     dict(good, recognizer='true'), dict(good, finals=['absent']),
                     dict(good, alphabet=['x','x']), dict(good, transitions={})]
        for data in mutations:
            with self.subTest(data=data):
                with self.assertRaises(core.InputError): core.from_dict(data)
        for cell in [[], ['q1'], ['ghost','0'], ['q1',{}], ['q1',True], ['q1','']]:
            data = copy.deepcopy(good)
            data['transitions']['q1']['x'] = cell
            with self.subTest(cell=cell):
                with self.assertRaises(core.InputError): core.from_dict(data)


if __name__ == '__main__':
    unittest.main()
