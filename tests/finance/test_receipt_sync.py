"""Synthetic regression checks for scanned-receipt analytics sync."""
import runpy
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / 'hosts/nexus/files/opt/data/bin/finance-receipt-sync'


class ReceiptSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = runpy.run_path(str(SCRIPT), run_name='finance_test')

    def sample(self):
        receipt = {
            'id': 7, 'merchant': 'Example Grocery', 'total': '10.50',
            'date': '2026-11-01',
            'items': [{'name': 'Apples', 'amount': '10.00'}],
        }
        archive = {
            'schemaVersion': 1, 'source': 'apple-cloud',
            'merchant': 'Example Grocery', 'total': '10.50',
            'date': '2026-11-01', 'currency': 'CAD',
            'subtotal': '10.00', 'taxes': [{'name': 'HST', 'amount': '0.50'}],
            'discounts': [],
            'items': [{'name': 'Apples', 'quantity': 2, 'unit': 'kg',
                       'unitPrice': '5.00', 'totalPrice': '10.00'}],
        }
        return receipt, archive

    def test_strict_matching_and_exact_arithmetic(self):
        receipt, archive = self.sample()
        select = self.api['select_archive']
        validate = self.api['validate_archive']
        self.assertIs(select(receipt, [(archive, 'a' * 64)]), archive)
        payload = validate(receipt, archive, 'a' * 64)
        self.assertEqual(payload['source_key'], '7')
        self.assertEqual((payload['subtotal_cents'], payload['tax_cents'],
                          payload['total_cents']), (1000, 50, 1050))
        self.assertEqual(payload['items'][0]['quantity'], '2')
        self.assertEqual(payload['items'][0]['line_total_cents'], 1000)

    def test_ambiguous_or_wrong_source_fails_closed(self):
        receipt, archive = self.sample()
        select = self.api['select_archive']
        self.assertIsNone(select(receipt, [(archive, 'a' * 64),
                                            (dict(archive), 'b' * 64)]))
        bad = dict(archive, total='10.51')
        self.assertIsNone(select(receipt, [(bad, 'a' * 64)]))
        with self.assertRaises(ValueError):
            self.api['validate_archive'](receipt, dict(archive, subtotal='9.00'),
                                         'a' * 64)

    def test_existing_source_hash_is_immutable(self):
        receipt, archive = self.sample()
        payload = self.api['validate_archive'](receipt, archive, 'a' * 64)
        classify = self.api['classify_existing']
        self.assertEqual(classify({'source_data': {'source_sha256': 'a' * 64}},
                                  payload), 'already')
        self.assertEqual(classify({'source_data': {'source_sha256': 'b' * 64}},
                                  payload), 'changed')
        self.assertEqual(classify(None, payload), 'new')

    def test_insert_script_uses_csv_copy_and_conflict_guard(self):
        receipt, archive = self.sample()
        payload = self.api['validate_archive'](receipt, archive, 'a' * 64)
        sql = self.api['build_insert_script'](payload)
        self.assertIn('COPY incoming (payload) FROM STDIN WITH (FORMAT csv)', sql)
        self.assertIn('ON CONFLICT (source, source_key) DO NOTHING', sql)
        self.assertIn('ON COMMIT DROP', sql)
        self.assertIn('COMMIT;', sql)
        self.assertNotIn('Example Grocery\' OR 1=1', sql)

    def test_psql_write_attaches_stdin(self):
        command = self.api['analytics_write_command']()
        self.assertEqual(command[:3], ['docker', 'exec', '-i'])
        self.assertEqual(command[-1], '-q')


if __name__ == '__main__':
    unittest.main()
