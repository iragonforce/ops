"""Synthetic tests for strict IMAP purchase-alert ingest and receipt candidates."""
from email.message import EmailMessage
import runpy
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / 'hosts/nexus/files/opt/data/bin/finance-mail-ingest'


def example(*, sender='CIBC <alerts@cibc.com>', auth='mx; dkim=pass header.d=cibc.com; spf=pass smtp.mailfrom=elsewhere.example', merchant='EXAMPLE MARKET'):
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = 'recipient@example.invalid'
    msg['Subject'] = 'New purchase on your credit card'
    msg['Date'] = 'Mon, 09 Nov 2026 13:00:00 -0500'
    msg['Message-ID'] = '<test-unique@example.invalid>'
    msg['Authentication-Results'] = auth
    msg.set_content('<html><body><p>You\u2019ve recently made a purchase with your CIBC Dividend Visa card ending in 1234 for $10.50 at ' + merchant + '</p></body></html>', subtype='html')
    return msg.as_bytes()


class MailIngestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = runpy.run_path(str(SCRIPT), run_name='mail_test')

    def test_strict_authenticated_parser(self):
        result = self.api['parse_alert'](example(), 123, 456)
        self.assertEqual(result['amount_cents'], 1050)
        self.assertEqual(result['merchant'], 'EXAMPLE MARKET')
        self.assertEqual((result['imap_uid'], result['uidvalidity']), (123, 456))
        self.assertEqual(len(result['source_key']), 64)
        self.assertNotIn('1234', str(result))  # card suffix never persisted

    def test_spoof_and_unsupported_subject_fail_closed(self):
        with self.assertRaises(ValueError):
            self.api['parse_alert'](example(auth='mx; dkim=pass header.d=attacker.invalid'), 123, 456)
        self.assertIsNone(self.api['parse_alert'](example(sender='Alerts <a@attacker.invalid>'), 123, 456))
        raw = example().replace(b'New purchase on your credit card', b'Your statement is ready')
        self.assertIsNone(self.api['parse_alert'](raw, 123, 456))

    def test_one_to_one_receipt_candidates_and_collisions(self):
        alert = self.api['parse_alert'](example(), 123, 456)
        receipt = {'id': 7, 'source': 'metro_email', 'merchant': 'EXAMPLE MARKET',
                   'date': '2026-11-09', 'total_cents': 1050, 'wrangler_receipt_id': None}
        matched = self.api['match_receipts']([alert], [receipt])
        self.assertEqual((matched[0]['match_state'], matched[0]['purchase_receipt_id'],
                          matched[0]['wrangler_receipt_id']), ('candidate', 7, None))
        scan = dict(receipt, id=8, source='wrangler_scan', wrangler_receipt_id=88)
        scanned = self.api['match_receipts']([alert], [scan])
        self.assertEqual((scanned[0]['purchase_receipt_id'], scanned[0]['wrangler_receipt_id']), (8, 88))
        second = dict(alert, source_key='b' * 64)
        collided = self.api['match_receipts']([alert, second], [receipt])
        self.assertTrue(all(x['match_state'] == 'review' and x['purchase_receipt_id'] is None for x in collided))
        self.assertEqual(self.api['match_receipts']([alert], [dict(receipt, total_cents=1051)])[0]['match_state'], 'unmatched')
        self.assertEqual(self.api['match_receipts']([alert], [receipt, scan])[0]['match_state'], 'review')

    def test_sql_batch_is_idempotent_and_private_values_are_stdin_only(self):
        alert = self.api['parse_alert'](example(), 123, 456)
        sql = self.api['build_insert_script']([alert])
        self.assertIn('CREATE TABLE IF NOT EXISTS transaction_email_alerts', sql)
        self.assertIn('purchase_receipt_id', sql)
        self.assertIn('CREATE OR REPLACE VIEW v_purchase_item_tracking', sql)
        self.assertIn('COPY incoming (payload) FROM STDIN WITH (FORMAT csv)', sql)
        self.assertIn('ON CONFLICT (source_key) DO NOTHING', sql)
        self.assertIn('COMMIT;', sql)
        self.assertEqual(self.api['analytics_write_command']()[:3], ['docker', 'exec', '-i'])


if __name__ == '__main__':
    unittest.main()
