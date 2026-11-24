"""Offline regressions for the three established Markdown point generators."""

import hashlib
import runpy
import tempfile
import unittest
import uuid
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


class HeadingChunkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = {
            name: runpy.run_path(str(SCRIPTS / filename)) for name, filename in (
                ('inbox', 'qdrant-memory.py'),
                ('ops', 'homelab-index-ops.py'),
                ('obsidian', 'obsidian-index.py'),
            )
        }

    def records(self, kind, content, name='fixture.md'):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / name
            path.write_text(content, encoding='utf-8')
            mod = self.modules[kind]
            if kind == 'inbox':
                return list(mod['chunks'](path, content))
            if kind == 'ops':
                return list(mod['chunks'](root))
            return list(mod['passages'](path, root))

    @staticmethod
    def expected_id(kind, ordinal, name='fixture.md'):
        if kind == 'obsidian':
            key = f'obsidian_history:secondBrain/Homelab/{name}:{ordinal}'
        elif kind == 'inbox':
            key = f'manual_inbox:{name}:{ordinal}'
        else:
            key = f'ops:{name}:{ordinal}'
        return str(uuid.uuid5(uuid.NAMESPACE_URL, key))

    def check_hashes(self, records):
        for _, payload in records:
            self.assertEqual(payload['content_sha256'], hashlib.sha256((
                payload['heading'] + '\n' + str(payload['line_start'])
                + '\n' + payload['text']
            ).encode()).hexdigest())

    def test_consecutive_and_empty_sections_preserve_original_ordinals(self):
        text = '# Root\n\n## Empty\n\n### Details\nOperational note.\n'
        for kind in self.modules:
            with self.subTest(kind=kind):
                results = self.records(kind, text)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0][0], self.expected_id(kind, 2))
                self.assertEqual((results[0][1]['line_start'], results[0][1]['line_end']), (1, 6))
                for phrase in ('# Root', '## Empty', '### Details', 'Operational note.'):
                    self.assertIn(phrase, results[0][1]['text'])
                self.check_hashes(results)

    def test_short_substantive_text_and_trailing_heading(self):
        text = '# Alpha\nOK\n## Beta\nYes\n## Tail\n'
        for kind in self.modules:
            with self.subTest(kind=kind):
                records = self.records(kind, text)
                self.assertEqual([pid for pid, _ in records],
                                 [self.expected_id(kind, 0), self.expected_id(kind, 1)])
                self.assertIn('OK', records[0][1]['text'])
                self.assertIn('Yes', records[1][1]['text'])
                self.assertNotIn('Tail', records[1][1]['text'])
                self.check_hashes(records)

    def test_cross_source_heading_is_not_attached_to_next_ops_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a.md').write_text('# A\nContent A.\n## Orphan\n', encoding='utf-8')
            (root / 'b.md').write_text('# B\nContent B.\n', encoding='utf-8')
            records = list(self.modules['ops']['chunks'](root))
        self.assertEqual(len(records), 2)
        b = next((pid, p) for pid, p in records if p['source'] == 'b.md')
        self.assertEqual(b[0], self.expected_id('ops', 0, 'b.md'))
        self.assertEqual(b[1]['heading'], 'B')
        self.assertEqual(b[1]['line_start'], 1)
        self.assertNotIn('Orphan', b[1]['text'])
        self.check_hashes(records)

    def test_limit_provenance_and_heading_fallback(self):
        for kind, mod in self.modules.items():
            maximum = mod['MAX_CHARS']
            # Outer is heading-only; the first substantive chunk begins on
            # line 2, and the prefix cannot fit without exceeding the limit.
            text = '# Outer\n## Inner\n' + 'X' * maximum + '\n'
            with self.subTest(kind=kind):
                results = self.records(kind, text)
                self.assertTrue(results)
                self.assertEqual(results[0][0], self.expected_id(kind, 1))
                for _, payload in results:
                    self.assertLessEqual(len(payload['text']), maximum)
                first = results[0][1]
                self.assertIn('Outer', first['heading'])
                self.assertIn('Inner', first['text'])
                self.assertEqual(first['line_start'], 2)
                self.assertEqual(first['line_end'], 3)
                self.check_hashes(results)

    def test_no_headings_and_empty_document(self):
        for kind in self.modules:
            with self.subTest(kind=kind):
                self.assertEqual(self.records(kind, ''), [])
                short = self.records(kind, 'A meaningful short note.\n')
                self.assertEqual(len(short), 1)
                self.assertEqual(short[0][0], self.expected_id(kind, 0))
                self.check_hashes(short)

    def test_previously_substantive_unchanged_id_and_hash(self):
        for kind, mod in self.modules.items():
            with self.subTest(kind=kind):
                content = '# Title\nA useful detail.\n'
                current = self.records(kind, content)
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / 'fixture.md'
                    path.write_text(content, encoding='utf-8')
                    if kind == 'inbox':
                        original = list(mod['_original_chunks'](path, content))
                    elif kind == 'ops':
                        original = list(mod['_original_chunks'](path.parent))
                    else:
                        original = list(mod['_original_passages'](path, path.parent))
                self.assertEqual(current, original)

    def test_inbox_plain_text_does_not_parse_hash_heading(self):
        result = self.records('inbox', '# Not a Markdown heading\nshort text\n', 'fixture.txt')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], self.expected_id('inbox', 0, 'fixture.txt'))
        self.check_hashes(result)


if __name__ == '__main__':
    unittest.main()
