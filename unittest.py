import unittest
import json
from flask_testing import TestCase
from your_flask_app import app, db, User, Role, user_datastore

class TestAutoScaler(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        db.create_all()
        db.session.commit()
        user_datastore.create_role(name='admin', description='Administrator')
        user_datastore.create_user(username='admin', password='admin', roles=['admin'])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_status(self):
        response = self.client.get('/app/status')
        self.assert200(response)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('cpu', data)
        self.assertIn('replicas', data)

    def test_update_replicas_without_authentication(self):
        response = self.client.put('/app/replicas', json={"replicas": 5})
        self.assert401(response)

    def test_update_replicas_with_authentication(self):
        # Authenticate as the admin user
        self.client.post('/login', data=dict(username='admin', password='admin'))

        # Update replicas without trigger_person (allowed since the change is <= 50)
        response = self.client.put('/app/replicas', json={"replicas": 10})
        self.assert200(response)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('message', data)
        self.assertEqual(data['message'], "Replica count updated to 10 by None")

        # Update replicas with trigger_person (required since the change is > 50)
        response = self.client.put('/app/replicas', json={"replicas": 60, "trigger_person": "John"})
        self.assert400(response)
        data = json.loads(response.data.decode('utf-8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], "Trigger person is required for changes greater than 50 replicas")

if __name__ == '__main__':
    unittest.main()
