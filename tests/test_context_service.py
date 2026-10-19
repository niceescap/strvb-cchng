"""Rollback-only PostgreSQL integration checks for context selections."""
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=True)
DATABASE_URL = os.getenv('DATABASE_URL', '')
if not DATABASE_URL or make_url(DATABASE_URL).database != 'coach_proto':
    raise RuntimeError('tests/test_context_service.py requires DATABASE_URL from project .env to name coach_proto')

sys.path.insert(0, str(ROOT))
import app as coach  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from services import context_service  # noqa: E402


class ContextServiceTests(unittest.TestCase):
    def setUp(self):
        try:
            self.connection = coach.engine.connect()
        except Exception as exc:
            raise unittest.SkipTest(f'connexion coach_proto indisponible ({type(exc).__name__})') from exc
        self.transaction = self.connection.begin()
        self.db = coach.SessionLocal(bind=self.connection, join_transaction_mode="create_savepoint")
        self.users = []
        for ix in range(2):
            self.users.append(self.db.execute(text(
                "INSERT INTO coach_users (email,password_hash,name,credit_micro_usd,model_choice) "
                "VALUES (:email,'test','Context Test',0,'demo') RETURNING id"
            ), {'email': f'context-test-{id(self)}-{ix}@example.invalid'}).scalar_one())
        self.activities = []
        for ix, uid in enumerate(self.users):
            self.activities.append(self.db.execute(text(
                "INSERT INTO coach_activities (user_id,title,occurred_at,sport) "
                "VALUES (:uid,'test',:occurred,'Ride') RETURNING id"
            ), {'uid': uid, 'occurred': datetime.now(timezone.utc)}).scalar_one())
        self.db.flush()

    def tearDown(self):
        try:
            self.db.close()
        finally:
            if self.transaction.is_active:
                self.transaction.rollback()
            self.connection.close()

    def test_create_and_increment_effective_changes(self):
        first = context_service.toggle_item(self.db, 'discussion-create', self.users[0],
                                            'activity', self.activities[0], True)
        self.assertEqual(first['context_version'], 1)
        second_id = self.db.execute(text(
            "INSERT INTO coach_activities (user_id,title,occurred_at,sport) "
            "VALUES (:uid,'second',:occurred,'Ride') RETURNING id"
        ), {'uid': self.users[0], 'occurred': datetime.now(timezone.utc)}).scalar_one()
        second = context_service.toggle_item(self.db, 'discussion-create', self.users[0], 'activity', second_id, True)
        self.assertEqual(second['context_version'], 2)

    def test_noop_keeps_version(self):
        context_service.toggle_item(self.db, 'discussion-noop', self.users[0],
                                    'activity', self.activities[0], True)
        result = context_service.toggle_item(self.db, 'discussion-noop', self.users[0],
                                             'activity', self.activities[0], True)
        self.assertEqual(result['context_version'], 1)

    def test_other_user_cannot_read_or_modify_discussion(self):
        context_service.toggle_item(self.db, 'discussion-private', self.users[0],
                                    'activity', self.activities[0], True)
        for operation in (
            lambda: context_service.get_selection(self.db, 'discussion-private', self.users[1]),
            lambda: context_service.toggle_item(self.db, 'discussion-private', self.users[1],
                                                'activity', self.activities[1], True),
        ):
            with self.assertRaises(HTTPException) as error:
                operation()
            self.assertEqual(error.exception.status_code, 404)

    def test_item_owned_by_other_user_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            context_service.toggle_item(self.db, 'discussion-item-owner', self.users[0],
                                        'activity', self.activities[1], True)
        self.assertEqual(error.exception.status_code, 404)

    def test_activity_limit_rejects_without_writes(self):
        previous = context_service.MAX_ACTIVITIES
        context_service.MAX_ACTIVITIES = 1
        try:
            context_service.toggle_item(self.db, 'discussion-limit', self.users[0],
                                        'activity', self.activities[0], True)
            with self.assertRaises(HTTPException) as error:
                context_service.toggle_item(self.db, 'discussion-limit', self.users[0],
                                            'activity', self._second_activity(), True)
            self.assertEqual(error.exception.status_code, 422)
            self.assertEqual(self.db.scalar(text(
                "SELECT count(*) FROM coach_chat_context_items WHERE discussion_id='discussion-limit'"
            )), 1)
            self.assertEqual(self.db.scalar(text(
                "SELECT context_version FROM coach_chat_contexts WHERE discussion_id='discussion-limit'"
            )), 1)
        finally:
            context_service.MAX_ACTIVITIES = previous

    def _second_activity(self):
        return self.db.execute(text(
            "INSERT INTO coach_activities (user_id,title,occurred_at,sport) "
            "VALUES (:uid,'second',:occurred,'Ride') RETURNING id"
        ), {'uid': self.users[0], 'occurred': datetime.now(timezone.utc)}).scalar_one()

    def test_invalid_item_type_is_422(self):
        with self.assertRaises(HTTPException) as error:
            context_service.toggle_item(self.db, 'discussion-type', self.users[0],
                                        'video', self.activities[0], True)
        self.assertEqual(error.exception.status_code, 422)


if __name__ == '__main__':
    unittest.main()
