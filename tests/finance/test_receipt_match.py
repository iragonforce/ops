"""Synthetic regression checks for candidate-only receipt ↔ bank matching."""
import runpy
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / 'hosts/nexus/files/opt/data/bin/finance-receipt-match'


class ReceiptMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = runpy.run_path(str(SCRIPT), run_name='finance_test')

    def receipt(self, ident=1, merchant='Example Grocery', amount=1050):
        return {'id': ident, 'source': 'wrangler_scan', 'merchant': merchant,
                'date': '2026-11-01', 'total_cents': amount}

    def activity(self, ident='11111111-1111-4111-8111-111111111111',
                 notes='EXAMPLE GROCERY STORE', amount='10.50', when='2026-11-02'):
        return {'id': ident, 'accountId': '22222222-2222-4222-8222-222222222222',
                'accountName': 'Example Account', 'activityType': 'WITHDRAWAL',
                'currency': 'CAD', 'amount': amount, 'date': when, 'notes': notes}

    def test_unique_exact_amount_near_date_strong_merchant(self):
        result = self.api['choose_unique_matches']([self.receipt()], [self.activity()])
        self.assertEqual(result['candidate_count'], 1)
        self.assertEqual(result['links'][0]['receipt_id'], 1)
        self.assertEqual(result['links'][0]['visible_spending_cents'], 1050)
        self.assertEqual(result['links'][0]['activity_type'], 'WITHDRAWAL')

    def test_wrong_amount_date_merchant_type_and_currency_rejected(self):
        failures = [self.activity(amount='10.51'),
                    self.activity(when='2026-11-05'),
                    self.activity(notes='Unrelated Fuel'),
                    dict(self.activity(), activityType='DEPOSIT'),
                    dict(self.activity(), currency='USD')]
        for wrong in failures:
            with self.subTest(wrong=wrong):
                self.assertEqual(self.api['choose_unique_matches'](
                    [self.receipt()], [wrong])['candidate_count'], 0)

    def test_same_receipt_ambiguous_or_activity_shared_across_receipts(self):
        other = self.activity(ident='33333333-3333-4333-8333-333333333333')
        result = self.api['choose_unique_matches']([self.receipt()],
                                                   [self.activity(), other])
        self.assertEqual(result['candidate_count'], 0)
        self.assertEqual(result['ambiguous_count'], 1)
        result = self.api['choose_unique_matches']([self.receipt(), self.receipt(2)],
                                                   [self.activity()])
        self.assertEqual(result['candidate_count'], 0)
        self.assertEqual(result['ambiguous_count'], 2)

    def test_non_finite_or_sub_cent_bank_amount_rejected(self):
        for amount in ('NaN', '10.501', 'Infinity'):
            with self.subTest(amount=amount):
                result = self.api['choose_unique_matches'](
                    [self.receipt()], [self.activity(amount=amount)])
                self.assertEqual(result['candidate_count'], 0)

    def test_existing_links_are_preserved_or_checked(self):
        activity = self.activity()
        link = self.api['choose_unique_matches']([self.receipt()], [activity])['links'][0]
        self.assertEqual(self.api['classify_existing'](
            {'receipt_id': 1, 'activity_id': activity['id'], 'match_state': 'candidate'},
            link), 'already')
        self.assertEqual(self.api['classify_existing'](
            {'receipt_id': 1, 'activity_id': activity['id'], 'match_state': 'confirmed'},
            link), 'preserve')
        self.assertEqual(self.api['classify_existing'](None, link), 'new')
        with self.assertRaises(ValueError):
            self.api['classify_existing'](
                {'receipt_id': 1, 'activity_id': '44444444-4444-4444-8444-444444444444',
                 'match_state': 'candidate'}, link)

    def test_previous_candidate_disappears_fail_closed(self):
        old = {'receipt_id': 1, 'activity_id': self.activity()['id'],
               'match_state': 'candidate',
               'match_method': 'unique_amount_merchant_near_date_v1'}
        with self.assertRaises(ValueError):
            self.api['reject_stale_candidates']([self.receipt()], [old],
                self.api['choose_unique_matches']([self.receipt()], []))
        self.api['reject_stale_candidates']([self.receipt()], [old],
            self.api['choose_unique_matches']([self.receipt()], [self.activity()]))
        self.api['reject_stale_candidates']([self.receipt()],
            [dict(old, match_state='confirmed')],
            self.api['choose_unique_matches']([self.receipt()], []))
        with self.assertRaises(ValueError):
            self.api['reject_stale_candidates']([], [old],
                self.api['choose_unique_matches']([], []))

    def test_sql_is_atomic_candidate_only_and_idempotent(self):
        link = self.api['choose_unique_matches']([self.receipt()],
                                                 [self.activity()])['links'][0]
        sql = self.api['build_insert_script']([link])
        self.assertIn('COPY incoming (payload) FROM STDIN WITH (FORMAT csv)', sql)
        self.assertIn('ON CONFLICT (activity_id) DO NOTHING', sql)
        self.assertIn('ON CONFLICT (receipt_id) DO NOTHING', sql)
        self.assertIn("'candidate'", sql)
        self.assertIn("'spending'", sql)
        self.assertIn('BEGIN;', sql)
        self.assertIn('COMMIT;', sql)
        self.assertEqual(self.api['analytics_write_command']()[:3], ['docker', 'exec', '-i'])


if __name__ == '__main__':
    unittest.main()
