"""Synthetic safety and idempotency checks for future-only finance mail posting."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[2] / 'hosts/nexus/files/opt/data/bin/finance-mail-post'
MAIL = Path(__file__).resolve().parents[2] / 'hosts/nexus/files/opt/data/bin/finance-mail-ingest'


def message(suffix='1234', auth='mail.protonmail.ch; dkim=pass header.d=cibc.com'):
    m = EmailMessage()
    m['From'] = 'CIBC <alerts@cibc.com>'
    m['To'] = 'recipient@example.invalid'
    m['Subject'] = 'New purchase on your credit card'
    m['Date'] = 'Wed, 11 Nov 2026 14:00:00 -0500'
    m['Message-ID'] = '<example-auto-post@example.invalid>'
    m['Authentication-Results'] = auth
    m.set_content('<html><body><p>You\u2019ve recently made a purchase with your CIBC Dividend Visa card ending in '
                  + suffix + ' for $10.50 at EXAMPLE MARKET</p></body></html>', subtype='html')
    return m.as_bytes()


class FinanceMailPostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib = runpy.run_path(str(SCRIPT), run_name='finance_mail_post_test')
        cls.mail = runpy.run_path(str(MAIL), run_name='finance_mail_ingest_test')

    def route(self):
        return {'schema': 'finance-mail-route-v1', 'sender_domain': 'cibc.com',
                'card_label': 'cibc dividend visa', 'card_suffix': '1234',
                'target_account_id': '11111111-1111-4111-8111-111111111111',
                'target_name_sha256': hashlib.sha256(b'CIBC Credit').hexdigest(),
                'historical_unique_strong_matches': 391, 'historical_other_account_matches': 0,
                'max_auto_amount_cents': 500000,
                'activated_at': '2026-11-11T12:00:00-05:00',
                'activation_utc': datetime(2026, 11, 11, 17, tzinfo=timezone.utc)}

    def test_route_authentication_suffix_and_label_fail_closed(self):
        original = self.mail['parse_alert'](message(), 4, 5)
        self.assertEqual(self.lib['route_from_message'](
            message(), 4, 5, self.mail, self.route(), original), original)
        for raw in (message(suffix='4321'), message(auth='attacker.invalid; dkim=pass header.d=cibc.com'),
                    message(auth='mail.protonmail.ch; dkim=pass header.d=attacker.invalid')):
            with self.assertRaises(ValueError):
                self.lib['route_from_message'](raw, 4, 5, self.mail, self.route(), original)
        account = {'id': self.route()['target_account_id'], 'accountType': 'CASH',
                   'currency': 'CAD', 'isActive': True, 'name': 'CIBC Credit'}
        self.assertEqual(self.lib['validate_account'](self.route(), [account]), account)
        with self.assertRaises(ValueError):
            self.lib['validate_account'](self.route(), [dict(account, name='Changed')])

    def test_one_to_one_decision_and_marker_recovery(self):
        key = 'a' * 64
        alert = {'source_key': key, 'received_at': '2026-11-11T14:00:00-05:00',
                 'amount_cents': 1050, 'merchant': 'EXAMPLE MARKET'}
        bank = {'id': 'uuid', 'activityType': 'WITHDRAWAL', 'currency': 'CAD',
                'amount': 10.50, 'date': '2026-11-11', 'notes': 'Example Market'}
        decide = self.lib['decide']
        strong = self.mail['strong']
        self.assertEqual(decide(alert, [], strong)[0], 'new')
        self.assertEqual(decide(alert, [bank], strong)[0], 'preexisting')
        self.assertEqual(decide(alert, [bank, dict(bank, id='other')], strong)[0], 'review')
        tagged = dict(bank, id='tagged', notes='Example Market [finance-mail:' + key + ']')
        self.assertEqual(decide(alert, [bank, tagged], strong), ('tagged', tagged))
        self.assertEqual(decide(alert, [dict(bank, amount=10.51)], strong)[0], 'new')
        self.assertTrue(self.lib['validate_saved'](dict(tagged, accountId=self.route()['target_account_id']),
            {'accountId': self.route()['target_account_id'], 'amount': 10.5, 'date': '2026-11-11'},
            'finance-mail:' + key))

    @unittest.skipUnless(os.geteuid() == 0, 'journal owner check requires root')
    def test_protected_journal_atomic_stages_and_uncertainty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'journals'
            path.mkdir(mode=0o700)
            globals_ = self.lib['journal_write'].__globals__
            old = globals_['JOURNALS']
            globals_['JOURNALS'] = path
            try:
                item = {'source_key': 'a' * 64, 'source_sha256': 'b' * 64, 'stage': 'precommit'}
                self.lib['journal_write'](item)
                self.assertEqual((path / ('a' * 64 + '.json')).stat().st_mode & 0o777, 0o600)
                self.assertEqual(self.lib['read_journal']('a' * 64)['stage'], 'precommit')
                with self.assertRaises(ValueError):
                    self.lib['journal_write'](item)
                self.lib['journal_write'](dict(item, stage='committed_unverified'), 'precommit')
                self.lib['journal_write'](dict(item, stage='posted'), 'committed_unverified')
                with self.assertRaises(ValueError):
                    self.lib['journal_write'](dict(item, stage='posted'), 'precommit')
            finally:
                globals_['JOURNALS'] = old

    @unittest.skipUnless(os.geteuid() == 0, 'journal owner check requires root')
    def test_synthetic_commit_and_repeat_does_not_recommit(self):
        key = 'a' * 64
        received = datetime.now(timezone.utc).isoformat()
        alert = {'source_key': key, 'source_sha256': 'b' * 64, 'received_at': received,
                 'merchant': 'EXAMPLE MARKET', 'amount_cents': 1050, 'currency': 'CAD',
                 'uidvalidity': 10, 'imap_uid': 3}
        route = dict(self.route(), activation_utc=datetime.now(timezone.utc)-timedelta(hours=1))
        target = route['target_account_id']
        account = {'id': target, 'name': 'CIBC Credit', 'isActive': True,
                   'accountType': 'CASH', 'currency': 'CAD'}
        saved = {'id': '22222222-2222-4222-8222-222222222222', 'accountId': target,
                 'activityType': 'WITHDRAWAL', 'date': received, 'currency': 'CAD',
                 'amount': 10.5, 'notes': 'EXAMPLE MARKET [finance-mail:' + key + ']'}
        class Fake:
            def __init__(self):
                self.commits = 0
            def initialize(self):
                pass
            def call(self, name, args):
                if name == 'get_accounts': return {'accounts': [account]}
                if name == 'prepare_activity_import':
                    return {'summary': {'total': 1, 'valid': 1, 'invalid': 0, 'duplicates': 0}}
                if name == 'commit_activity_import':
                    self.commits += 1
                    return {'summary': {'imported': 1},
                            'financialRows': [{'activityId': saved['id'], 'financialStatus': 'imported'}]}
                raise AssertionError(name)
        fake = Fake()
        mail = {'credentials': lambda: ('user', 'password'),
                'read_alerts': lambda _u, _p: ([alert], {'review': 0}),
                'strong': self.mail['strong']}
        def load(name, run_name):
            return mail if name == self.lib['MAIL_SOURCE'] else {'MCP': lambda _token: fake}
        @contextmanager
        def writer(_helper):
            yield fake
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'journals'
            path.mkdir(mode=0o700)
            globals_ = self.lib['run'].__globals__
            previous = globals_['JOURNALS']
            globals_['JOURNALS'] = path
            try:
                with mock.patch.dict(globals_, {
                    'load_route': lambda: route,
                    'staged_alerts': lambda _activated: {key: alert},
                    'fetch_new_identity': lambda *args: None,
                    'secret_by_key': lambda _key: 'redacted',
                    'temporary_write_client': writer,
                }), mock.patch('runpy.run_path', side_effect=load), mock.patch.dict(
                    globals_, {'all_activities': mock.Mock(side_effect=[[], [saved], [saved]])}):
                    self.lib['run'](True)
                    self.lib['run'](True)
                self.assertEqual(fake.commits, 1)
                self.assertEqual(self.lib['read_journal'](key)['stage'], 'posted')
            finally:
                globals_['JOURNALS'] = previous

if __name__ == '__main__':
    unittest.main()
