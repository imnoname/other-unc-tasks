import unittest
from finite_automaton_synth import synthesize


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        self.automaton = synthesize('a⟨b⟩⟨(c|d)⟩⟨e⟩')

    def test_states_and_accepting_states(self):
        self.assertEqual(self.automaton.states, ['q0', 'q1', 'q2', 'q3'])
        self.assertEqual(self.automaton.accepting, {'q1', 'q2', 'q3'})

    def test_transitions(self):
        expected = {
            ('q0', 'a'): 'q1',
            ('q1', 'b'): 'q1', ('q1', 'c'): 'q2', ('q1', 'd'): 'q2', ('q1', 'e'): 'q3',
            ('q2', 'c'): 'q2', ('q2', 'd'): 'q2', ('q2', 'e'): 'q3',
            ('q3', 'e'): 'q3',
        }
        self.assertEqual(self.automaton.transitions, expected)

    def test_acceptance_and_rejection(self):
        for word in ('a', 'abbb', 'acdeee', 'ade', 'abce'):
            with self.subTest(word=word):
                self.assertTrue(self.automaton.accepts(word))
        for word in ('', 'ba', 'acb', 'aeb'):
            with self.subTest(word=word):
                self.assertFalse(self.automaton.accepts(word))

    def test_non_variant_expression_synthesis(self):
        expression = 'x⟨(y|z)⟩'
        automaton = synthesize(expression)
        self.assertTrue(automaton.accepts('x'))
        self.assertTrue(automaton.accepts('xyzy'))
        self.assertFalse(automaton.accepts('yx'))


if __name__ == '__main__':
    unittest.main()
