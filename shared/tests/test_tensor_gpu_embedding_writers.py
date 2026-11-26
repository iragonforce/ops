"""Offline fail-closed integration checks for Nexus writer and MCP search paths."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


writer = load('tensor_test_memory_writer', 'qdrant-memory.py')
mcp = load('tensor_test_memory_mcp', 'qdrant-memory-hermes-mcp.py')


class NexusEmbeddingAdmissionTest(unittest.TestCase):
    def test_writer_does_not_contact_ollama_or_qdrant_on_handoff_failure(self):
        record = [('00000000-0000-0000-0000-000000000001',
                   {'source': 'ops/file.md', 'heading': 'heading', 'text': 'body'})]
        with patch.dict(os.environ, {'QDRANT_MEMORY_EMBED_COMMAND': '["/missing/command"]'}), \
                patch.object(writer, 'request', side_effect=AssertionError('direct network bypass')):
            with self.assertRaises(RuntimeError):
                writer.upsert(record)

    def test_mcp_search_fails_before_qdrant_query_on_handoff_failure(self):
        with patch.dict(os.environ, {'QDRANT_MEMORY_EMBED_COMMAND': '["/missing/command"]'}), \
                patch.object(mcp, 'post', side_effect=AssertionError('direct network bypass')):
            with self.assertRaises(RuntimeError):
                mcp.search({'query': 'a technical question'})

    def test_original_direct_writer_path_when_no_transport_is_configured(self):
        vectors = [[0.5] * writer.DIMENSIONS]
        calls = []
        def request(url, data=None, method=None):
            calls.append(url)
            if url.endswith('/api/embed'):
                return {'embeddings': vectors}
            return {'status': 'ok'}
        record = [('00000000-0000-0000-0000-000000000001',
                   {'source': 'ops/file.md', 'heading': 'heading', 'text': 'body'})]
        with patch.dict(os.environ, {}, clear=True), patch.object(writer, 'request', side_effect=request):
            writer.upsert(record)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].endswith('/api/embed'))
        self.assertIn('points?wait=true', calls[1])


if __name__ == '__main__':
    unittest.main()
