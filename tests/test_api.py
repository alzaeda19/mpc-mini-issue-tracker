"""Integration checks through HTTP against isolated, real SQLite databases."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import create_app


class IssueApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'test.db')
        self.client = TestClient(create_app(self.path), raise_server_exceptions=False)
        self.client.__enter__()
        self.payload = dict(title='Fix login', description='Login fails on mobile',
                            status='Open', priority='High', assignee_id=1)

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def create(self, **changes):
        response = self.client.post('/api/issues', json={**self.payload, **changes})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_crud_and_dates(self):
        issue = self.create()
        url = f'/api/issues/{issue["id"]}'
        self.assertEqual(self.client.get(url).json(), issue)
        self.assertEqual(issue['created_at'], issue['updated_at'])
        response = self.client.patch(url, json={'status': 'Resolved', 'assignee_id': 2, 'title': 'Fixed'})
        self.assertEqual(response.status_code, 200)
        updated = response.json()
        self.assertEqual(updated['status'], 'Resolved')
        self.assertEqual(updated['assignee_id'], 2)
        self.assertEqual(updated['title'], 'Fixed')
        self.assertEqual(updated['description'], issue['description'])
        self.assertEqual(updated['created_at'], issue['created_at'])
        self.assertGreater(updated['updated_at'], issue['updated_at'])
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)

    def test_search_status_and_pagination(self):
        first = self.create()
        second = self.create(title='UI polish', description='Improve contrast', status='Closed')
        self.assertEqual(len(self.client.get('/api/issues').json()), 2)
        self.assertEqual(self.client.get('/api/issues?status=Open&search=MOBILE').json(), [first])
        self.assertEqual(self.client.get('/api/issues?status=Closed&search=login').json(), [])
        self.assertEqual(self.client.get('/api/issues?search=polish').json(), [second])
        self.assertEqual(self.client.get('/api/issues?limit=1&offset=1').json(), [first])
        self.assertEqual(self.client.get('/api/issues?search=%25').json(), [])
        self.assertEqual(self.client.get('/api/issues?search=%27%20OR%201=1').json(), [])

    def test_invalid_create(self):
        for changes in [dict(title='  '), dict(description=' '), dict(status='Unknown'),
                        dict(priority='Urgent'), dict(assignee_id=999), dict(assignee_id=0),
                        dict(assignee_id=True), dict(title='x' * 201), dict(title=None), dict(extra='bad')]:
            with self.subTest(changes=changes):
                response = self.client.post('/api/issues', json={**self.payload, **changes})
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.post('/api/issues', json={}).status_code, 422)
        self.assertEqual(self.client.get('/api/issues').json(), [])

    def test_invalid_patch_leaves_issue_unchanged(self):
        issue = self.create()
        url = f'/api/issues/{issue["id"]}'
        for changes in [{}, {'title': ''}, {'status': None}, {'priority': 'Urgent'},
                        {'assignee_id': 999}, {'created_at': 'fake'}]:
            with self.subTest(changes=changes):
                self.assertEqual(self.client.patch(url, json=changes).status_code, 422)
                self.assertEqual(self.client.get(url).json(), issue)

    def test_invalid_ids_and_queries(self):
        for issue_id in ['abc', '0', '-1']:
            for method in ['get', 'delete']:
                self.assertEqual(getattr(self.client, method)(f'/api/issues/{issue_id}').status_code, 422)
        self.assertEqual(self.client.patch('/api/issues/999', json={'status': 'Closed'}).status_code, 404)
        for query in ['status=Bad', 'limit=0', 'limit=101', 'offset=-1']:
            self.assertEqual(self.client.get('/api/issues?' + query).status_code, 422)

    def test_users_and_restart_persistence(self):
        users = self.client.get('/api/users').json()
        self.assertEqual([user['id'] for user in users], [1, 2, 3])
        issue = self.create()
        with TestClient(create_app(self.path)) as restarted:
            self.assertEqual(restarted.get(f'/api/issues/{issue["id"]}').json(), issue)
            self.assertEqual(restarted.get('/api/users').json(), users)

    def test_safe_storage_and_unexpected_errors(self):
        with patch('app.repository.Repository.list', side_effect=sqlite3.OperationalError('private SQL')):
            response = self.client.get('/api/issues')
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('private SQL', response.text)
        with patch('app.repository.Repository.get', side_effect=RuntimeError('private stack')):
            response = self.client.get('/api/issues/1')
            self.assertEqual(response.status_code, 500)
            self.assertNotIn('private stack', response.text)

    def test_frontend_and_docs_are_served(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertIn('Mini Issue Tracker', self.client.get('/').text)
        self.assertEqual(self.client.get('/static/app.js').status_code, 200)
        self.assertEqual(self.client.get('/docs').status_code, 200)


if __name__ == '__main__':
    unittest.main()
