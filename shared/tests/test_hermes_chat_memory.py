"""Regression checks for Gemini-selected, forward-only Hermes chat findings."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest import mock

SCRIPTS = Path(__file__).parents[1] / 'scripts'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError('missing test module')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chat = load('hermes_chat_test', SCRIPTS / 'hermes_chat_memory.py')
core = load('qdrant_chat_test', SCRIPTS / 'qdrant-memory.py')
mcp = load('qdrant_chat_mcp_test', SCRIPTS / 'qdrant-memory-hermes-mcp.py')


class ChatMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'state.db'
        self.now = time.time()
        self.user = ('For the Qdrant memory project, keep the existing collection and '
                     'record that the indexing check passed after deployment.')
        self.answer = ('The indexing check passed against the existing Qdrant collection '
                       'and a repeated run added no duplicate points. This was observed, '
                       'not inferred from an earlier proposal.')
        conn = sqlite3.connect(self.db)
        conn.executescript('''
            CREATE TABLE sessions (id TEXT PRIMARY KEY, profile_name TEXT, source TEXT,
                ended_at REAL, end_reason TEXT);
            CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT,
                content TEXT, timestamp REAL, finish_reason TEXT, active INTEGER,
                compacted INTEGER, _compressed_summary INTEGER, display_kind TEXT,
                tool_calls TEXT);
        ''')
        self.conn = conn
        self.add_turn('default-ok', 'default', 'tui', 10, self.user, self.answer)
        self.add_turn('other-profile', 'research', 'tui', 20, self.user, self.answer)
        self.add_turn('cron-job', 'default', 'cron', 30, self.user, self.answer)
        self.add_turn('delegate', 'default', 'subagent', 40, self.user, self.answer)
        self.add_turn('failed', 'default', 'cli', 50, self.user, self.answer, failed=True)
        self.add_turn('interrupted', 'default', 'photon', 60, self.user, self.answer, finish=None)
        conn.commit()

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()

    def add_turn(self, session, profile, source, msg_id, user, answer, *, failed=False,
                 finish: str | None='stop', age=300, ended_at=None, end_reason='tui_close'):
        self.conn.execute('INSERT OR IGNORE INTO sessions VALUES (?,?,?,?,?)',
                          (session, profile, source, self.now-10 if ended_at is None else ended_at, end_reason))
        self.conn.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                          (msg_id, session, 'user', user, self.now-age-1, None, 1, 0, 0, None, None))
        self.conn.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                          (msg_id+1, session, 'assistant', answer, self.now-age, finish, 1, 0, 0, None, None))
        if failed:
            self.conn.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                              (msg_id+2, session, 'assistant', 'Failure', self.now-age+1,
                               None, 1, 0, 0, 'failed_turn', None))

    def test_only_settled_default_human_turns(self):
        rows = chat.settled_turns(self.db, 0, now=self.now)
        self.assertEqual([(r[0], r[1], r[2]) for r in rows], [(11, 'default-ok', 10)])
        self.add_turn('too-new', 'default', 'tui', 70, self.user, self.answer, age=30)
        self.conn.commit()
        self.assertEqual(len(chat.settled_turns(self.db, 0, now=self.now)), 1)
        self.assertEqual(chat.newest_message_id(self.db), 71)
        self.assertEqual(chat.settled_turns(self.db, 11, now=self.now), [])

    def test_closed_sessions_skip_open_and_compression_without_losing_later_closes(self):
        self.add_turn('open', 'default', 'tui', 100, self.user, self.answer, ended_at=0)
        self.conn.execute("UPDATE sessions SET ended_at=NULL, end_reason=NULL WHERE id='open'")
        self.add_turn('compressed', 'default', 'tui', 110, self.user, self.answer, end_reason='compression')
        self.add_turn('later-close', 'default', 'tui', 120, self.user, self.answer, ended_at=self.now)
        self.conn.commit()
        cursor = (self.now-20, '', chat.FINISHED_SESSION)
        page = chat.closed_turns(self.db, cursor, limit=1)
        self.assertEqual([row[1] for row, _ in page if row], ['default-ok'])
        later = chat.closed_turns(self.db, page[-1][1], limit=8)
        self.assertEqual([row[1] for row, _ in later if row], ['later-close'])
        self.assertEqual(chat.closed_turns(self.db, later[-1][1]), [])
        self.conn.execute("UPDATE sessions SET ended_at=?, end_reason='tui_close' WHERE id='open'", (self.now+1,))
        self.conn.commit()
        self.assertEqual([row[1] for row, _ in chat.closed_turns(self.db, later[-1][1]) if row], ['open'])

    def test_closed_session_paginates_each_turn_without_advancing_past_unread_rows(self):
        self.add_turn('default-ok', 'default', 'tui', 200, self.user, self.answer)
        self.conn.commit()
        cursor = (self.now-20, '', chat.FINISHED_SESSION)
        ids = []
        for _ in range(4):
            page = chat.closed_turns(self.db, cursor, limit=1)
            if not page:
                break
            ids.extend(row[0] for row, _ in page if row)
            cursor = page[-1][1]
        self.assertEqual(ids, [11, 201])
        self.assertEqual(cursor[2], chat.FINISHED_SESSION)

    def test_sensitive_and_oversized_chats_never_sent(self):
        self.assertTrue(chat.safe_pair(self.user, self.answer, (core.SENSITIVE,)))
        self.assertFalse(chat.safe_pair('password=<redacted> ' + self.user, self.answer,
                                        (core.SENSITIVE,)))
        self.assertFalse(chat.safe_pair('mail me at test@example.org ' + self.user, self.answer,
                                        (core.SENSITIVE,)))
        self.assertFalse(chat.safe_pair(self.user, self.answer + 'A'*9000, (core.SENSITIVE,)))

    def test_finding_schema_and_provenance(self):
        turn = chat.settled_turns(self.db, 0, now=self.now)[0]
        fact = {'topic': 'Qdrant indexing check',
                'text': 'The Qdrant indexer passed an observed deployment check, and a second pass created no duplicate points.'}
        records = chat.build_records(turn, [fact], (core.SENSITIVE,))
        self.assertEqual(len(records), 1)
        pid, payload = records[0]
        self.assertEqual(payload['origin'], 'hermes_chat')
        self.assertEqual(payload['authority'], 'conversation_historical_unverified')
        self.assertTrue(payload['historical_only'])
        self.assertNotIn(self.user, json.dumps(payload))
        self.assertEqual(pid, chat.build_records(turn, [fact], (core.SENSITIVE,))[0][0])
        self.assertEqual(chat.build_records(turn, [{'topic': fact['topic'], 'text': 'token=<redacted> and ' + fact['text']}], (core.SENSITIVE,)), [])
        self.assertEqual(chat.build_records(turn, [{'topic': 'password in heading', 'text': fact['text']}], (core.SENSITIVE,)), [])
        self.assertIn('hermes_chat', mcp.ALLOWED_ORIGINS)
        self.assertEqual(mcp.origin_authority(payload), payload['authority'])

    def test_model_output_is_schema_checked(self):
        plugin = self.root / 'plugin'
        plugin.mkdir()
        class Completion:
            def __init__(self, content):
                self.choices = [type('Choice', (), {'finish_reason': 'stop',
                    'message': type('Message', (), {'content': content, 'tool_calls': None})()})()]
        class Client:
            def __enter__(self):return self
            def __exit__(self, *_):pass
            chat = type('Chat', (), {'completions': type('Completions', (), {
                'create': staticmethod(lambda **_: Completion('{"facts": []}'))})()})()
        with mock.patch.object(chat.importlib, 'import_module', return_value=type('Plugin', (), {'AntigravityClient': Client})):
            self.assertEqual(chat.select_facts(self.user, self.answer, plugin_dir=plugin), [])
        with mock.patch.object(chat.importlib, 'import_module', return_value=type('Plugin', (), {
                'AntigravityClient': type('BadClient', (Client,), {'chat': type('Chat', (), {
                    'completions': type('Completions', (), {'create': staticmethod(lambda **_: Completion('{"facts": "not a list"}'))})()})()})})):
            with self.assertRaisesRegex(ValueError, 'schema'):
                chat.select_facts(self.user, self.answer, plugin_dir=plugin)

    def test_checkpoint_idempotency_failure_and_readback(self):
        fact = {'topic': 'Qdrant indexing check',
                'text': 'The Qdrant indexer passed an observed deployment check, and a second pass created no duplicate points.'}
        store = {}
        state = self.root / 'state'
        state.mkdir(mode=0o700)
        def existing(origin):
            return {pid: payload for pid, payload in store.items() if payload['origin'] == origin}
        def upsert(records):
            store.update(records)
        context = [mock.patch.object(core, 'STATE', state),
                   mock.patch.object(core, 'INDEXERS', SCRIPTS),
                   mock.patch.dict(os.environ, {'QDRANT_MEMORY_HERMES_DB': str(self.db)}),
                   mock.patch.object(core, 'verify_collection'),
                   mock.patch.object(core, 'existing_points', side_effect=existing),
                   mock.patch.object(core, 'upsert', side_effect=upsert)]
        with context[0], context[1], context[2], context[3], context[4], context[5]:
            with self.assertRaisesRegex(RuntimeError, 'bootstrap'):
                core.sync_chat()
            cursor = (self.now-20, '', chat.FINISHED_SESSION)
            core.closed_checkpoint_write(cursor)
            with mock.patch.object(core.chat, 'select_facts', side_effect=OSError('provider unavailable')):
                with self.assertRaisesRegex(RuntimeError, 'chat selector failed .OSError.'):
                    core.sync_chat()
                self.assertEqual(core.closed_checkpoint_read(), cursor)
            with mock.patch.object(core.chat, 'select_facts', return_value=[fact]):
                core.sync_chat()
                self.assertEqual(len(store), 1)
                self.assertEqual(core.closed_checkpoint_read()[1], 'interrupted')
                core.sync_chat()
                self.assertEqual(len(store), 1)
            checkpoint = state / 'hermes-closed-chat-checkpoint.json'
            self.assertEqual(checkpoint.stat().st_mode & 0o777, 0o600)
            leftover = state / 'hermes-closed-chat-checkpoint.tmp'
            leftover.write_text('interrupted private staging')
            leftover.chmod(0o600)
            core.closed_checkpoint_write(core.closed_checkpoint_read())
            self.assertFalse(leftover.exists())
            invalid = json.loads(checkpoint.read_text())
            invalid['cursor'][2] = 42
            checkpoint.write_text(json.dumps(invalid))
            with self.assertRaisesRegex(RuntimeError, 'integrity'):
                core.closed_checkpoint_read()


if __name__ == '__main__':
    unittest.main()
