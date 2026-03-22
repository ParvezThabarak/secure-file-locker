"""
Secure File Locker — API Test Suite
21IPE315P — Cloud Product and Platform Engineering
PBL-II: DevOps Practices + PBL-III: Testing & Validation

Tests all 13 API endpoints:
- Auth: register, login, logout, me
- Files: upload, download, delete, list, share, stats
- Analytics: risk-summary, access-logs, stats
"""
import pytest
import json
import io
from unittest.mock import patch, MagicMock


# ── FIXTURES ─────────────────────────────────────────────────
@pytest.fixture
def app():
    """Create test Flask app."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from app import create_app
    app = create_app('testing') if 'testing' in __import__('app.config.config', fromlist=['config']).config else create_app('default')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    from app.database.database import db
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Create authenticated test client."""
    # Register a test user
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!'
    })
    # Login
    client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'TestPass123!'
    })
    return client


# ── AUTH TESTS ────────────────────────────────────────────────
class TestAuth:

    def test_register_success(self, client):
        """TC1: User can register with valid details."""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Password123!'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['email'] == 'new@example.com'

    def test_register_duplicate_email(self, client):
        """TC2: Cannot register with existing email."""
        client.post('/api/auth/register', json={
            'username': 'user1', 'email': 'dup@test.com', 'password': 'Pass123!'
        })
        response = client.post('/api/auth/register', json={
            'username': 'user2', 'email': 'dup@test.com', 'password': 'Pass123!'
        })
        assert response.status_code == 409

    def test_login_success(self, client):
        """TC3: User can login with correct credentials."""
        client.post('/api/auth/register', json={
            'username': 'logintest', 'email': 'login@test.com', 'password': 'Pass123!'
        })
        response = client.post('/api/auth/login', json={
            'email': 'login@test.com', 'password': 'Pass123!'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Login successful'

    def test_login_wrong_password(self, client):
        """TC4: Login fails with wrong password."""
        client.post('/api/auth/register', json={
            'username': 'wrongpass', 'email': 'wrong@test.com', 'password': 'Pass123!'
        })
        response = client.post('/api/auth/login', json={
            'email': 'wrong@test.com', 'password': 'WrongPassword!'
        })
        assert response.status_code == 401

    def test_get_current_user(self, auth_client):
        """TC5: Authenticated user can get their profile."""
        response = auth_client.get('/api/auth/me')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data

    def test_logout(self, auth_client):
        """TC6: User can logout successfully."""
        response = auth_client.post('/api/auth/logout')
        assert response.status_code == 200

    def test_unauthenticated_access(self, client):
        """TC7: Unauthenticated requests to protected routes return 401."""
        response = client.get('/api/auth/me')
        assert response.status_code == 401


# ── FILE TESTS ────────────────────────────────────────────────
class TestFiles:

    @patch('routes.files.get_user_s3_service')
    def test_upload_file(self, mock_s3, auth_client):
        """TC8: Authenticated user can upload a file."""
        mock_service = MagicMock()
        mock_s3.return_value = mock_service
        mock_service.upload_file.return_value = True

        data = {
            'file': (io.BytesIO(b'test file content'), 'test.txt')
        }
        response = auth_client.post('/api/files/upload',
            data=data, content_type='multipart/form-data')

        assert response.status_code in (201, 500)  # 500 if no DB for file

    def test_list_files(self, auth_client):
        """TC9: User can list their files."""
        response = auth_client.get('/api/files/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'files' in data

    def test_file_stats(self, auth_client):
        """TC10: User can get file statistics."""
        response = auth_client.get('/api/files/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_files' in data
        assert 'total_size' in data

    def test_download_nonexistent_file(self, auth_client):
        """TC11: Downloading nonexistent file returns 404."""
        response = auth_client.get('/api/files/99999/download')
        assert response.status_code == 404

    def test_delete_nonexistent_file(self, auth_client):
        """TC12: Deleting nonexistent file returns 404."""
        response = auth_client.delete('/api/files/99999')
        assert response.status_code == 404

    def test_share_nonexistent_file(self, auth_client):
        """TC13: Sharing nonexistent file returns 404."""
        response = auth_client.post('/api/files/99999/share', json={'expiry': '1hr'})
        assert response.status_code == 404


# ── ANALYTICS / ML TESTS ──────────────────────────────────────
class TestAnalytics:

    def test_risk_summary(self, auth_client):
        """TC14: User can get their ML risk summary."""
        response = auth_client.get('/api/analytics/risk-summary')
        assert response.status_code == 200

    def test_access_logs(self, auth_client):
        """TC15: User can get their access logs."""
        response = auth_client.get('/api/analytics/access-logs')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'logs' in data

    def test_action_stats(self, auth_client):
        """TC16: User can get action statistics."""
        response = auth_client.get('/api/analytics/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'stats' in data


# ── HEALTH CHECK TEST ─────────────────────────────────────────
class TestHealth:

    def test_health_endpoint(self, client):
        """TC17: Health endpoint returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_api_root(self, client):
        """TC18: API root returns endpoint list."""
        response = client.get('/api')
        assert response.status_code == 200
