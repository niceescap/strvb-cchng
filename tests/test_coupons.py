"""Coupon redemption tests. All fixture writes are contained in rolled-back transactions."""
import hashlib
import hmac
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=True)
DATABASE_URL = os.getenv('DATABASE_URL', '')
if not DATABASE_URL or make_url(DATABASE_URL).database != 'coach_proto':
    raise RuntimeError('tests/test_coupons.py requires DATABASE_URL from project .env to name coach_proto; no writes were made')

sys.path.insert(0, str(ROOT))
import app as coach  # noqa: E402

TEST_HMAC_SECRET = 'coupon-test-secret-only-not-from-env-123456'


class CouponTests(unittest.TestCase):
    def setUp(self):
        self.connection = coach.engine.connect()
        self.transaction = self.connection.begin()
        self.db = coach.SessionLocal(bind=self.connection)
        self.users = []
        for ix in range(2):
            result = self.db.execute(text("INSERT INTO coach_users (email,password_hash,name,credit_micro_usd,model_choice) VALUES (:email,'test','Coupon Test',0,'demo') RETURNING id"), {'email': f'coupon-test-{id(self)}-{ix}@example.invalid'})
            self.users.append(result.scalar_one())
        self.db.flush()

    def tearDown(self):
        try:
            self.db.close()
        finally:
            if self.transaction.is_active:
                self.transaction.rollback()
            self.connection.close()

    def coupon(self, code, amount=1234567, active=True, expires=None, max_redemptions=1):
        digest = hmac.new(TEST_HMAC_SECRET.encode(), code.encode(), hashlib.sha256).hexdigest()
        cid = self.db.execute(text('INSERT INTO coupons (code_hash,amount_micro_usd,expires_at,max_redemptions,active) VALUES (:h,:amount,:expires,:maximum,:active) RETURNING id'), {
            'h': digest, 'amount': amount, 'expires': expires or datetime.now(timezone.utc) + timedelta(days=1), 'maximum': max_redemptions, 'active': active,
        }).scalar_one()
        return cid

    def redeem(self, uid, code):
        coupon = coach.redeem_coupon.__wrapped__ if hasattr(coach.redeem_coupon, '__wrapped__') else coach.redeem_coupon
        from starlette.requests import Request
        request = Request({'type': 'http', 'method': 'POST', 'path': '/api/credits/redeem', 'headers': [(b'cookie', b'coach_credit_csrf=csrf')], 'client': ('test', 1), 'server': ('test', 80), 'scheme': 'https', 'query_string': b'', 'root_path': '', 'http_version': '1.1'})
        user = self.db.execute(text('SELECT * FROM coach_users WHERE id=:uid'), {'uid': uid}).mappings().first()
        try:
            return coupon(request, code, 'csrf', user, self.db)
        except Exception as exc:
            return exc

    def balance(self, uid):
        return self.db.execute(text('SELECT credit_micro_usd FROM coach_users WHERE id=:uid'), {'uid': uid}).scalar_one()

    def assert_ledger_matches(self, uid):
        ledger = self.db.execute(text('SELECT coalesce(sum(delta_micro_usd),0) FROM credit_ledger WHERE user_id=:uid'), {'uid': uid}).scalar_one()
        self.assertEqual(self.balance(uid), ledger)

    def test_valid_coupon_credits_exact_amount_and_ledger(self):
        cid = self.coupon('TEST-VALID')
        coach.os.environ['COUPON_HMAC_SECRET'] = TEST_HMAC_SECRET
        result = self.redeem(self.users[0], ' TEST-VALID ')
        self.assertEqual(result['credit_micro_usd'], 1234567)
        self.assertEqual(result['message'], 'Crédit ajouté : 1.23 $')
        row = self.db.execute(text("SELECT delta_micro_usd,reason,request_id,note FROM credit_ledger WHERE user_id=:uid"), {'uid': self.users[0]}).mappings().one()
        self.assertEqual((row['delta_micro_usd'], row['reason'], row['request_id'], row['note']), (1234567, 'grant', f'coupon-{cid}-{self.users[0]}', 'coupon'))
        self.assert_ledger_matches(self.users[0])

    def test_duplicate_user_redemption_refused_without_balance_change(self):
        self.coupon('TEST-ONCE')
        coach.os.environ['COUPON_HMAC_SECRET'] = TEST_HMAC_SECRET
        self.assertIsInstance(self.redeem(self.users[0], 'TEST-ONCE'), dict)
        result = self.redeem(self.users[0], 'TEST-ONCE')
        self.assertEqual(result.status_code, 400)
        self.assertEqual(self.balance(self.users[0]), 1234567)
        self.assert_ledger_matches(self.users[0])

    def test_expired_inactive_unknown_same_generic_message(self):
        self.coupon('TEST-EXPIRED', expires=datetime.now(timezone.utc) - timedelta(days=1))
        self.coupon('TEST-INACTIVE', active=False)
        coach.os.environ['COUPON_HMAC_SECRET'] = TEST_HMAC_SECRET
        errors = [self.redeem(self.users[0], code) for code in ('TEST-EXPIRED', 'TEST-INACTIVE', 'UNKNOWN-CODE')]
        self.assertTrue(all(e.status_code == 400 for e in errors))
        self.assertEqual({e.detail for e in errors}, {coach.COUPON_FAILURE})
        self.assertEqual(self.balance(self.users[0]), 0)
        self.assert_ledger_matches(self.users[0])

    def test_redemption_limit_blocks_second_user(self):
        self.coupon('TEST-LIMIT', max_redemptions=1)
        coach.os.environ['COUPON_HMAC_SECRET'] = TEST_HMAC_SECRET
        self.assertIsInstance(self.redeem(self.users[0], 'TEST-LIMIT'), dict)
        denied = self.redeem(self.users[1], 'TEST-LIMIT')
        self.assertEqual(denied.status_code, 400)
        self.assertEqual(denied.detail, coach.COUPON_FAILURE)
        self.assertEqual(self.balance(self.users[1]), 0)
        self.assert_ledger_matches(self.users[0])
        self.assert_ledger_matches(self.users[1])

    def test_plain_code_is_not_stored_in_any_coupon_or_ledger_table(self):
        plain = 'PLAINTEXT-NEVER-STORE'
        self.coupon(plain)
        coach.os.environ['COUPON_HMAC_SECRET'] = TEST_HMAC_SECRET
        self.redeem(self.users[0], plain)
        found = self.db.execute(text("SELECT (SELECT count(*) FROM coupons WHERE code_hash=:code) + (SELECT count(*) FROM credit_ledger WHERE note=:code OR request_id=:code)"), {'code': plain}).scalar_one()
        self.assertEqual(found, 0)

    @unittest.skip('nécessite une base de test dédiée')
    def test_concurrent_redemption(self):
        pass


if __name__ == '__main__':
    unittest.main()
