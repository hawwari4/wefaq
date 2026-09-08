import os
import sys
import unittest
from datetime import date

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)
os.environ['WEFAQ_SEED_DEMO'] = 'false'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from models import CompatibilityRequest, MCQAnswer, Notification, SavedCandidate, User, UserProfile, db


class MatchInteractionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.drop_all()
            db.create_all()
            users = [
                User(code='MATCH-M', full_name='رجل', birthday=date(1994, 1, 1), gender='ذكر', country='قطر', status='approved'),
                User(code='MATCH-F', full_name='امرأة', birthday=date(1996, 1, 1), gender='أنثى', country='قطر', status='approved'),
                User(code='MATCH-F2', full_name='امرأة ثانية', birthday=date(1997, 1, 1), gender='أنثى', country='قطر', status='approved'),
            ]
            db.session.add_all(users)
            db.session.flush()
            for user in users:
                db.session.add(UserProfile(user_id=user.id, details={
                    'nationality': 'قطري', 'profession': 'مهندس', 'marital_status': 'لم أتزوج من قبل',
                    'marriage_timeline': '3 أشهر', 'height': 170, 'age_min': 18, 'age_max': 80,
                }))
                db.session.add(MCQAnswer(user_id=user.id, answers={'q1': 'بكالوريوس'}))
            db.session.commit()
            cls.male_id, cls.female_id, cls.second_female_id = [user.id for user in users]

    def setUp(self):
        with self.app.app_context():
            CompatibilityRequest.query.delete()
            SavedCandidate.query.delete()
            Notification.query.delete()
            db.session.commit()

    def headers(self, code):
        return {'X-User-Code': code}

    def test_request_is_persisted_notified_and_acceptance_is_private(self):
        created = self.client.post('/api/matching/requests', json={'candidate_id': self.female_id}, headers=self.headers('MATCH-M'))
        self.assertEqual(created.status_code, 201)
        request_id = created.get_json()['request']['id']
        with self.app.app_context():
            self.assertEqual(Notification.query.filter_by(user_id=self.female_id).count(), 1)

        incoming = self.client.get('/api/matching/requests', headers=self.headers('MATCH-F')).get_json()['incoming'][0]
        self.assertEqual(incoming['status'], 'pending')
        self.assertNotIn('full_name', incoming['candidate'])
        accepted = self.client.put(f'/api/matching/requests/{request_id}', json={'status': 'accepted'}, headers=self.headers('MATCH-F'))
        self.assertEqual(accepted.status_code, 200)
        sent = self.client.get('/api/matching/requests', headers=self.headers('MATCH-M')).get_json()['sent'][0]
        self.assertEqual(sent['status'], 'accepted')
        self.assertNotIn('phone', sent['candidate'])

    def test_duplicate_reciprocal_self_and_ineligible_requests_are_blocked(self):
        first = self.client.post('/api/matching/requests', json={'candidate_id': self.female_id}, headers=self.headers('MATCH-M'))
        duplicate = self.client.post('/api/matching/requests', json={'candidate_id': self.female_id}, headers=self.headers('MATCH-M'))
        reciprocal = self.client.post('/api/matching/requests', json={'candidate_id': self.male_id}, headers=self.headers('MATCH-F'))
        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(reciprocal.status_code, 200)
        with self.app.app_context():
            self.assertEqual(CompatibilityRequest.query.count(), 1)
        self.assertEqual(self.client.post('/api/matching/requests', json={'candidate_id': self.male_id}, headers=self.headers('MATCH-M')).status_code, 400)
        self.assertEqual(self.client.post('/api/matching/requests', json={'candidate_id': self.second_female_id}, headers=self.headers('MATCH-F')).status_code, 400)

    def test_only_receiver_can_respond(self):
        created = self.client.post('/api/matching/requests', json={'candidate_id': self.female_id}, headers=self.headers('MATCH-M')).get_json()
        response = self.client.put(f"/api/matching/requests/{created['request']['id']}", json={'status': 'accepted'}, headers=self.headers('MATCH-M'))
        self.assertEqual(response.status_code, 403)

    def test_saved_candidates_are_private_idempotent_and_removable(self):
        first = self.client.post('/api/matching/saved', json={'candidate_id': self.female_id}, headers=self.headers('MATCH-M'))
        second = self.client.post('/api/matching/saved', json={'candidate_id': self.female_id}, headers=self.headers('MATCH-M'))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        with self.app.app_context():
            self.assertEqual(SavedCandidate.query.count(), 1)
        own = self.client.get('/api/matching/saved', headers=self.headers('MATCH-M')).get_json()['saved']
        other = self.client.get('/api/matching/saved', headers=self.headers('MATCH-F')).get_json()['saved']
        self.assertEqual(len(own), 1)
        self.assertEqual(other, [])
        self.assertEqual(self.client.delete(f'/api/matching/saved/{self.female_id}', headers=self.headers('MATCH-M')).status_code, 200)

    def test_endpoints_require_an_approved_authenticated_user(self):
        self.assertEqual(self.client.get('/api/matching/requests').status_code, 403)
        self.assertEqual(self.client.get('/api/matching/saved').status_code, 403)


if __name__ == '__main__':
    unittest.main()
