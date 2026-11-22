import json
import tkinter as tk
import unittest


class GuiTests(unittest.TestCase):
    def test_json_parser_resource_errors_are_reported(self):
        import app
        root=tk.Tk(); root.withdraw()
        try:
            a=app.App(root)
            for text in ['1'*5000,'['*10000+'0'+']'*10000]:
                a.set_source('Мили JSON',text)
                a.build()
                self.assertIsNone(a.machine)
                self.assertIn('Ошибка',a.status.get())
        finally: root.destroy()

    def test_build_trace_error_and_recovery(self):
        import app
        self.assertTrue(hasattr(app,'App'))
        root=tk.Tk(); root.withdraw()
        try:
            a=app.App(root)
            a.set_source('РВ','a<b|c>d'); a.build()
            self.assertEqual(len(a.small.states),4)
            a.word.set('ad'); a.check_word()
            self.assertIn('ДОПУСТИМО',a.word_output.get('1.0','end'))
            a.set_source('РВ','a|'); a.build()
            self.assertIsNone(a.machine)
            self.assertIn('Ошибка',a.status.get())
            a.word.set('ad'); a.check_word()
            self.assertIn('Сначала',a.status.get())
            a.example_lecture()
            self.assertEqual(len(a.small.states),3)
            a.clear()
            self.assertIsNone(a.machine)
        finally:
            root.destroy()


if __name__=='__main__': unittest.main()
