import unittest


class CoreContract(unittest.TestCase):
    def test_synthesis_contract(self):
        import core
        self.assertTrue(hasattr(core, 'synthesize'))
        m = core.synthesize('a<b|c>d')
        for word, expected in [('ad', True), ('abcd', True), ('ab', False), ('', False), ('add', False)]:
            with self.subTest(word=word):
                self.assertEqual(core.run(m, word)['accepted'], expected)

    def test_lecture_contract(self):
        import core
        self.assertTrue(hasattr(core, 'lecture_machine'))
        m = core.lecture_machine()
        small, parts, mapping = core.minimize(m)
        self.assertEqual(len(m.states), 5)
        self.assertEqual(len(small.states), 3)
        self.assertEqual(parts[0], [['q1', 'q2'], ['q3'], ['q4', 'q5']])
        self.assertEqual(core.run(small, 'xyx')['outputs'], ['1', '0', '2'])
        self.assertTrue(core.compare(m, small)['equivalent'])


if __name__ == '__main__':
    unittest.main()
