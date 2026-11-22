import json
import tempfile
from pathlib import Path
import unittest
import core


class StorageTests(unittest.TestCase):
    def test_load_expression_and_mealy(self):
        import storage
        self.assertTrue(hasattr(storage, 'load_input'))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.txt'; p.write_text('a<b|c>d',encoding='utf-8-sig')
            mode, text=storage.load_input(p)
            self.assertEqual((mode,text),('РВ','a<b|c>d'))
            p=Path(d)/'input.json'; p.write_text(json.dumps(core.lecture_machine().to_dict()),encoding='utf-8')
            self.assertEqual(storage.load_input(p)[0],'Мили JSON')

    def test_exports_reopen_and_file_errors(self):
        import storage
        self.assertTrue(hasattr(storage, 'export_bundle'))
        with tempfile.TemporaryDirectory() as d:
            m=core.synthesize('a<b|c>d'); small,parts,mapping=core.minimize(m)
            storage.export_bundle(Path(d)/'out',m,small,parts,mapping)
            for name in ['original.json','minimal.json']:
                loaded=core.from_dict(json.loads((Path(d)/'out'/name).read_text(encoding='utf-8')))
                self.assertTrue(core.compare(m,loaded)['equivalent'])
            self.assertIn('Матрица', (Path(d)/'out/protocol.txt').read_text(encoding='utf-8'))
            self.assertTrue((Path(d)/'out/minimal.svg').exists())
            with self.assertRaises(core.InputError): storage.load_input(Path(d)/'missing')
            bad=Path(d)/'bad.txt'; bad.write_bytes(b'\xff\xfe\xff')
            with self.assertRaises(core.InputError): storage.load_input(bad)
            big=Path(d)/'big.txt'; big.write_bytes(b'x'*32_000_001)
            with self.assertRaises(core.InputError): storage.load_input(big)
            block=Path(d)/'block'; block.write_text('occupied')
            with self.assertRaises(core.InputError): storage.export_bundle(block,m,small,parts,mapping)


if __name__=='__main__': unittest.main()
