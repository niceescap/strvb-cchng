"""Rollback-only PostgreSQL integration tests for discussion context payloads."""
import os
import json
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=True)
DATABASE_URL = os.getenv('DATABASE_URL', '')
if not DATABASE_URL or make_url(DATABASE_URL).database != 'coach_proto':
    raise RuntimeError('tests/test_context_payload.py requires project .env DATABASE_URL naming coach_proto')

sys.path.insert(0, str(ROOT))
import app as coach  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from services import context_payload  # noqa: E402


class ContextPayloadTests(unittest.TestCase):
    def setUp(self):
        try:
            self.connection = coach.engine.connect()
        except Exception as exc:
            raise unittest.SkipTest(f'connexion coach_proto indisponible ({type(exc).__name__})') from exc
        self.transaction = self.connection.begin()
        self.db = coach.Session(bind=self.connection, join_transaction_mode='create_savepoint')
        self.users = []
        for ix in range(2):
            self.users.append(self.db.execute(text(
                "INSERT INTO coach_users (email,password_hash,name,credit_micro_usd,model_choice,ftp_watts,weight_kg,max_heartrate) "
                "VALUES (:email,'hash','private name',999,'private-model',250,70.5,190) RETURNING id"
            ), {'email': f'payload-{id(self)}-{ix}@example.invalid'}).scalar_one())
        base_time = datetime(2025, 2, 3, tzinfo=timezone.utc)
        self.activities = []
        for ix, (uid, occurred, summary) in enumerate((
            (self.users[0], base_time + timedelta(days=1), {'fv': 1, 'km': 25}),
            (self.users[0], base_time, None),
            (self.users[1], base_time, {'fv': 1}),
        )):
            self.activities.append(self.db.execute(text(
                "INSERT INTO coach_activities (user_id,title,occurred_at,sport,compact_json) "
                "VALUES (:uid,:title,:occurred,'Ride',CAST(:summary AS json)) RETURNING id"
            ), {'uid': uid, 'title': f'activity-{ix}', 'occurred': occurred,
                'summary': None if summary is None else __import__('json').dumps(summary)}).scalar_one())
        self.artifact_ids = []
        for ix, uid in enumerate(self.users):
            self.artifact_ids.append(self.db.execute(text(
                "INSERT INTO coach_artifacts (user_id,title,created_at,category,markdown) "
                "VALUES (:uid,:title,:created,'note','body') RETURNING id"
            ), {'uid': uid, 'title': f'artifact-{ix}', 'created': base_time}).scalar_one())

    def tearDown(self):
        try:
            self.db.close()
        finally:
            if self.transaction.is_active:
                self.transaction.rollback()
            self.connection.close()

    def _context(self, discussion, uid, version=7):
        self.db.execute(text(
            "INSERT INTO coach_chat_contexts (discussion_id,user_id,context_version) VALUES (:d,:u,:v)"
        ), {'d': discussion, 'u': uid, 'v': version})

    def _select(self, discussion, item_type, item_id):
        self.db.execute(text(
            "INSERT INTO coach_chat_context_items (discussion_id,item_type,item_id) VALUES (:d,:t,:i)"
        ), {'d': discussion, 't': item_type, 'i': item_id})

    def test_payload_contains_only_allowed_athlete_fields_and_exact_version(self):
        self._context('payload-fields', self.users[0], version=13)
        payload = context_payload.build_context(self.db, 'payload-fields', self.users[0])
        self.assertEqual(payload['context_version'], 13)
        self.assertEqual(payload['athlete'], {'ftp_watts': 250, 'weight_kg': 70.5, 'max_heartrate': 190})
        self.assertEqual(set(payload['athlete']), {'ftp_watts', 'weight_kg', 'max_heartrate'})

    def test_only_owner_selections_and_stable_order_and_missing_summary(self):
        discussion = 'payload-filter-order'
        self._context(discussion, self.users[0], version=4)
        self._select(discussion, 'activity', self.activities[0])
        self._select(discussion, 'activity', self.activities[1])
        self._select(discussion, 'activity', self.activities[2])  # foreign owned row must be filtered
        self._select(discussion, 'artifact', self.artifact_ids[0])
        self._select(discussion, 'artifact', self.artifact_ids[1])
        payload = context_payload.build_context(self.db, discussion, self.users[0])
        self.assertEqual([a['id'] for a in payload['activities']], [self.activities[1], self.activities[0]])
        self.assertEqual(payload['activities'][0]['resume'], None)
        self.assertTrue(payload['activities'][0]['resume_manquant'])
        self.assertEqual([a['id'] for a in payload['artifacts']], [self.artifact_ids[0]])

    def test_unknown_compact_version_is_marked(self):
        self._context('payload-unknown-version', self.users[0])
        self._select('payload-unknown-version', 'activity', self.activities[0])
        self.db.execute(text("UPDATE coach_activities SET compact_json=CAST(:summary AS json) WHERE id=:id"),
                        {'summary': json.dumps({'fv': 999}), 'id': self.activities[0]})
        payload = context_payload.build_context(self.db, 'payload-unknown-version', self.users[0])
        self.assertTrue(payload['activities'][0]['resume']['version_inconnue'])

    def test_foreign_discussion_is_404(self):
        self._context('payload-other-user', self.users[1])
        with self.assertRaises(HTTPException) as error:
            context_payload.build_context(self.db, 'payload-other-user', self.users[0])
        self.assertEqual(error.exception.status_code, 404)

    def test_token_limit_is_422_without_partial_payload(self):
        self._context('payload-large', self.users[0])
        self._select('payload-large', 'artifact', self.artifact_ids[0])
        self.db.execute(text("UPDATE coach_artifacts SET markdown=:body WHERE id=:id"),
                        {'body': 'x' * 5000, 'id': self.artifact_ids[0]})
        previous = context_payload.MAX_TOKENS_CONTEXT
        context_payload.MAX_TOKENS_CONTEXT = 10
        try:
            with self.assertRaises(HTTPException) as error:
                context_payload.build_context(self.db, 'payload-large', self.users[0])
            self.assertEqual(error.exception.status_code, 422)
            self.assertIn('estimation', error.exception.detail)
            self.assertIn('10', error.exception.detail)
        finally:
            context_payload.MAX_TOKENS_CONTEXT = previous

    def test_discussion_without_selections_has_empty_lists(self):
        self._context('payload-empty', self.users[0], version=0)
        payload = context_payload.build_context(self.db, 'payload-empty', self.users[0])
        self.assertEqual(payload['activities'], [])
        self.assertEqual(payload['artifacts'], [])


if __name__ == '__main__':
    unittest.main()
