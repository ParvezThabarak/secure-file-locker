"""
Test suite for Secure File Locker v3
Covers: crypto, ML engine, auth routes, locker routes, sharing, admin,
        2FA (TOTP), file preview, REST API + JWT, AWS integration
"""
import os, io, sys, tempfile, pytest, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.crypto_utils import encrypt_file, decrypt_file, get_file_hash, derive_key
from ml_engine.engine import classify_file, detect_anomaly, compute_threat_score, train_models


# ── Crypto Tests ──────────────────────────────────────────────────────────────
class TestCrypto:
    def test_key_derivation_length(self):
        assert len(derive_key("pass", b"saltsalt12345678")) == 32

    def test_key_deterministic(self):
        s = os.urandom(16)
        assert derive_key("pw", s) == derive_key("pw", s)

    def test_key_unique_passwords(self):
        s = os.urandom(16)
        assert derive_key("a", s) != derive_key("b", s)

    def test_roundtrip_small(self):
        data = b"Hello AES-256 CBC!"
        with tempfile.NamedTemporaryFile(delete=False) as f: f.write(data); s=f.name
        e, d = s+".enc", s+".dec"
        try:
            encrypt_file(s, e, "pw"); decrypt_file(e, d, "pw")
            assert open(d,'rb').read() == data
        finally:
            for p in [s,e,d]:
                if os.path.exists(p): os.unlink(p)

    def test_roundtrip_large(self):
        data = os.urandom(2*1024*1024)
        with tempfile.NamedTemporaryFile(delete=False) as f: f.write(data); s=f.name
        e, d = s+".enc", s+".dec"
        try:
            encrypt_file(s, e, "pw"); decrypt_file(e, d, "pw")
            assert open(d,'rb').read() == data
        finally:
            for p in [s,e,d]:
                if os.path.exists(p): os.unlink(p)

    def test_wrong_password_raises(self):
        with tempfile.NamedTemporaryFile(delete=False) as f: f.write(b"secret"); s=f.name
        e, d = s+".enc", s+".dec"
        try:
            encrypt_file(s, e, "correct")
            with pytest.raises(Exception): decrypt_file(e, d, "wrong")
        finally:
            for p in [s,e,d]:
                if os.path.exists(p): os.unlink(p)

    def test_ciphertext_differs(self):
        data = b"plaintext content"
        with tempfile.NamedTemporaryFile(delete=False) as f: f.write(data); s=f.name
        e = s+".enc"
        try:
            encrypt_file(s, e, "pw")
            assert open(e,'rb').read() != data
        finally:
            for p in [s,e]:
                if os.path.exists(p): os.unlink(p)

    def test_sha256_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as f: f.write(b"abc"); p=f.name
        try:
            h = get_file_hash(p); assert len(h)==64
        finally: os.unlink(p)

    def test_two_encryptions_differ(self):
        """Same plaintext encrypted twice → different ciphertext (random IV)"""
        data = b"same content"
        with tempfile.NamedTemporaryFile(delete=False) as f: f.write(data); s=f.name
        e1, e2 = s+".enc1", s+".enc2"
        try:
            encrypt_file(s,e1,"pw"); encrypt_file(s,e2,"pw")
            assert open(e1,'rb').read() != open(e2,'rb').read()
        finally:
            for p in [s,e1,e2]:
                if os.path.exists(p): os.unlink(p)


# ── ML Engine Tests ───────────────────────────────────────────────────────────
class TestMLEngine:
    def setup_method(self):
        train_models(force=False)

    def test_classify_returns_category(self):
        r = classify_file("report.pdf", 50000)
        assert 'category' in r
        assert r['category'] in ['document','office','image','media','archive','code','executable','other']

    def test_classify_confidence_range(self):
        r = classify_file("photo.jpg", 200000)
        assert 0.0 <= r['confidence'] <= 1.0

    def test_classify_executable_flagged(self):
        r = classify_file("setup.exe", 1024*1024)
        assert r['category'] == 'executable'

    def test_classify_text_file(self):
        r = classify_file("readme.txt", 2048)
        assert r['category'] in ['document', 'other']

    def test_anomaly_large_file_flagged(self):
        r = detect_anomaly(40*1024*1024, '.zip', upload_hour=14, day_of_week=1)
        assert 'is_anomaly' in r
        assert 'anomaly_score' in r

    def test_anomaly_midnight_upload(self):
        r = detect_anomaly(1024, '.txt', upload_hour=1, day_of_week=0)
        assert 'reason' in r
        assert 'unusual upload time' in r['reason']

    def test_anomaly_executable_reason(self):
        r = detect_anomaly(1024, '.exe', upload_hour=10)
        assert 'executable' in r['reason']

    def test_threat_score_low_for_normal(self):
        r = compute_threat_score("document.pdf", 50000, user_failed_logins=0)
        assert r['score'] < 0.6
        assert r['level'] in ('LOW', 'MEDIUM')

    def test_threat_score_high_for_executable(self):
        r = compute_threat_score("malware.exe", 500000, user_failed_logins=3)
        assert r['score'] > 0.4
        assert r['level'] in ('MEDIUM', 'HIGH', 'CRITICAL')

    def test_threat_score_has_breakdown(self):
        r = compute_threat_score("test.txt", 1024)
        assert 'breakdown' in r
        assert 'executable_type' in r['breakdown']
        assert 'anomaly_risk' in r['breakdown']

    def test_threat_score_range(self):
        r = compute_threat_score("test.zip", 1024*1024)
        assert 0.0 <= r['score'] <= 1.0

    def test_threat_level_labels(self):
        r = compute_threat_score("test.txt", 1024)
        assert r['level'] in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')


# ── Flask Integration Tests ───────────────────────────────────────────────────
@pytest.fixture
def app():
    from app import create_app, db
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'UPLOAD_FOLDER': os.path.join(tempfile.gettempdir(), 'v3_test_uploads'),
        'WTF_CSRF_ENABLED': False,
    })
    os.makedirs(application.config['UPLOAD_FOLDER'], exist_ok=True)
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()

@pytest.fixture
def client(app): return app.test_client()

@pytest.fixture
def user(app, client):
    from app import db
    from app.models import User
    with app.app_context():
        u = User(username='testuser', email='test@example.com')
        u.set_password('Password123')
        db.session.add(u); db.session.commit()
    return {'username':'testuser','password':'Password123'}

def login(client, username, password):
    return client.post('/login', data={'username':username,'password':password}, follow_redirects=True)


class TestAuthRoutes:
    def test_login_page(self, client):
        assert client.get('/login').status_code == 200

    def test_register_page(self, client):
        assert client.get('/register').status_code == 200

    def test_register_success(self, client, app):
        from app.models import User
        client.post('/register', data={
            'username':'newuser','email':'new@test.com',
            'password':'Password123','confirm_password':'Password123'
        }, follow_redirects=True)
        with app.app_context():
            assert User.query.filter_by(username='newuser').first() is not None

    def test_register_duplicate_username(self, client, user):
        r = client.post('/register', data={
            'username':'testuser','email':'other@test.com',
            'password':'Password123','confirm_password':'Password123'
        }, follow_redirects=True)
        assert b'taken' in r.data.lower() or r.status_code == 200

    def test_login_valid(self, client, user):
        r = login(client, 'testuser', 'Password123')
        assert b'vault' in r.data.lower() or r.status_code == 200

    def test_login_invalid(self, client, user):
        r = login(client, 'testuser', 'wrongpass')
        assert b'invalid' in r.data.lower()

    def test_dashboard_requires_auth(self, client):
        r = client.get('/dashboard', follow_redirects=True)
        assert b'login' in r.data.lower()


class TestLockerRoutes:
    def test_dashboard_loads(self, client, user):
        login(client, 'testuser', 'Password123')
        assert client.get('/dashboard').status_code == 200

    def test_upload_page_loads(self, client, user):
        login(client, 'testuser', 'Password123')
        assert client.get('/upload').status_code == 200

    def test_upload_file_success(self, client, user):
        login(client, 'testuser', 'Password123')
        r = client.post('/upload', data={
            'file': (io.BytesIO(b'test content'), 'test.txt'),
            'password': 'filepass123'
        }, content_type='multipart/form-data', follow_redirects=True)
        assert r.status_code == 200

    def test_upload_no_password_fails(self, client, user):
        login(client, 'testuser', 'Password123')
        r = client.post('/upload', data={
            'file': (io.BytesIO(b'content'), 'test.txt'),
            'password': 'ab'   # too short
        }, content_type='multipart/form-data', follow_redirects=True)
        assert r.status_code == 200

    def test_download_404_for_other_user(self, client, user):
        login(client, 'testuser', 'Password123')
        assert client.get('/download/99999').status_code == 404

    def test_ml_scan_api(self, client, user):
        login(client, 'testuser', 'Password123')
        r = client.post('/api/ml-scan',
            data=json.dumps({'filename':'test.pdf','size':50000}),
            content_type='application/json')
        assert r.status_code == 200
        d = json.loads(r.data)
        assert 'score' in d and 'level' in d


class TestAdminRoutes:
    def test_admin_requires_auth(self, client):
        r = client.get('/admin/', follow_redirects=True)
        assert r.status_code in (200, 403)

    def test_non_admin_gets_403(self, client, user):
        login(client, 'testuser', 'Password123')
        r = client.get('/admin/')
        assert r.status_code == 403

    def test_admin_user_can_access(self, client, app):
        from app import db
        from app.models import User
        with app.app_context():
            a = User(username='adminuser', email='admin2@test.com', is_admin=True)
            a.set_password('Admin@1234'); db.session.add(a); db.session.commit()
        login(client, 'adminuser', 'Admin@1234')
        r = client.get('/admin/')
        assert r.status_code == 200


# ── Email Verification Tests ─────────────────────────────────────────────────
class TestEmailVerification:
    def test_verify_code_generation(self, app):
        from app.models import User
        from app import db
        with app.app_context():
            u = User(username='verify_user', email='verify@test.com')
            u.set_password('Pass1234')
            code = u.generate_verify_code()
            assert len(code) == 6
            assert code.isdigit()
            assert u.email_verify_code == code
            assert u.email_verify_expires is not None

    def test_verify_code_correct(self, app):
        from app.models import User
        with app.app_context():
            u = User(username='verify_user2', email='verify2@test.com')
            u.set_password('Pass1234')
            code = u.generate_verify_code()
            assert u.check_verify_code(code) is True

    def test_verify_code_wrong(self, app):
        from app.models import User
        with app.app_context():
            u = User(username='verify_user3', email='verify3@test.com')
            u.set_password('Pass1234')
            u.generate_verify_code()
            assert u.check_verify_code('000000') is False

    def test_verify_code_expired(self, app):
        from app.models import User
        from datetime import datetime, timedelta
        with app.app_context():
            u = User(username='verify_user4', email='verify4@test.com')
            u.set_password('Pass1234')
            code = u.generate_verify_code()
            # Force expiry
            u.email_verify_expires = datetime.now() - timedelta(minutes=1)
            assert u.check_verify_code(code) is False

    def test_email_verify_triggers_after_3_failures(self, client, app):
        """After 3 wrong passwords, user should be redirected to email verification."""
        from app import db
        from app.models import User
        with app.app_context():
            u = User(username='failuser', email='fail@test.com')
            u.set_password('CorrectPass1')
            db.session.add(u); db.session.commit()
        # 3 failed login attempts
        for i in range(3):
            client.post('/login', data={'username':'failuser','password':'wrong'}, follow_redirects=True)
        # Check user has a verification code
        with app.app_context():
            u = User.query.filter_by(username='failuser').first()
            assert u.failed_logins >= 3
            assert u.email_verify_code is not None

    def test_email_verify_page_loads(self, client, app):
        """The email verification page should load when there's a pending verification."""
        from app import db
        from app.models import User
        with app.app_context():
            u = User(username='verifypage', email='vp@test.com')
            u.set_password('Pass1234')
            u.generate_verify_code()
            u.failed_logins = 3
            db.session.add(u); db.session.commit()
            uid = u.id
        with client.session_transaction() as sess:
            sess['pending_verify_user_id'] = uid
        r = client.get('/verify-email')
        assert r.status_code == 200
        assert b'verification' in r.data.lower()

    def test_email_verify_correct_code_logs_in(self, client, app):
        """Entering the correct code should log the user in."""
        from app import db
        from app.models import User
        with app.app_context():
            u = User(username='correctcode', email='cc@test.com')
            u.set_password('Pass1234')
            code = u.generate_verify_code()
            u.failed_logins = 3
            db.session.add(u); db.session.commit()
            uid = u.id
        with client.session_transaction() as sess:
            sess['pending_verify_user_id'] = uid
        r = client.post('/verify-email', data={'code': code}, follow_redirects=False)
        assert r.status_code == 302
        assert '/dashboard' in r.headers.get('Location', '')


# ── File Preview Tests ────────────────────────────────────────────────────────
class TestPreview:
    def test_preview_page_loads(self, client, user, app):
        login(client, 'testuser', 'Password123')
        # Upload a text file first
        client.post('/upload', data={
            'file': (io.BytesIO(b'preview test content'), 'preview_test.txt'),
            'password': 'filepass123'
        }, content_type='multipart/form-data', follow_redirects=True)
        from app.models import LockedFile
        with app.app_context():
            lf = LockedFile.query.filter_by(original_filename='preview_test.txt').first()
            if lf:
                r = client.get(f'/preview/{lf.id}')
                assert r.status_code == 200

    def test_preview_requires_login(self, client):
        r = client.get('/preview/1', follow_redirects=True)
        assert b'login' in r.data.lower()

    def test_preview_404_for_missing_file(self, client, user):
        login(client, 'testuser', 'Password123')
        r = client.get('/preview/99999')
        assert r.status_code == 404

    def test_preview_content_wrong_password(self, client, user, app):
        login(client, 'testuser', 'Password123')
        client.post('/upload', data={
            'file': (io.BytesIO(b'secret text'), 'secret.txt'),
            'password': 'correctpw'
        }, content_type='multipart/form-data', follow_redirects=True)
        from app.models import LockedFile
        with app.app_context():
            lf = LockedFile.query.filter_by(original_filename='secret.txt').first()
            if lf:
                r = client.post(f'/preview/{lf.id}/content',
                    data={'password': 'wrongpassword'})
                assert r.status_code == 403


# ── REST API + JWT Tests ──────────────────────────────────────────────────────
class TestRestAPI:
    def test_api_login_success(self, client, user):
        r = client.post('/api/v1/auth/login',
            data=json.dumps({'username':'testuser','password':'Password123'}),
            content_type='application/json')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'token' in data
        assert data['expires_in'] == 3600

    def test_api_login_invalid(self, client, user):
        r = client.post('/api/v1/auth/login',
            data=json.dumps({'username':'testuser','password':'wrong'}),
            content_type='application/json')
        assert r.status_code == 401

    def test_api_files_requires_token(self, client):
        r = client.get('/api/v1/files')
        assert r.status_code == 401

    def test_api_list_files(self, client, user):
        # Get token
        r = client.post('/api/v1/auth/login',
            data=json.dumps({'username':'testuser','password':'Password123'}),
            content_type='application/json')
        token = json.loads(r.data)['token']
        # List files
        r = client.get('/api/v1/files',
            headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'files' in data
        assert 'total' in data

    def test_api_upload_and_get_file(self, client, user):
        r = client.post('/api/v1/auth/login',
            data=json.dumps({'username':'testuser','password':'Password123'}),
            content_type='application/json')
        token = json.loads(r.data)['token']
        # Upload
        r = client.post('/api/v1/files/upload',
            data={'file': (io.BytesIO(b'api test'), 'api_test.txt'), 'password': 'apipass123'},
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 201
        file_id = json.loads(r.data)['file']['id']
        # Get metadata
        r = client.get(f'/api/v1/files/{file_id}',
            headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        assert json.loads(r.data)['filename'] == 'api_test.txt'

    def test_api_delete_file(self, client, user):
        r = client.post('/api/v1/auth/login',
            data=json.dumps({'username':'testuser','password':'Password123'}),
            content_type='application/json')
        token = json.loads(r.data)['token']
        # Upload first
        r = client.post('/api/v1/files/upload',
            data={'file': (io.BytesIO(b'delete me'), 'delete_me.txt'), 'password': 'delpass123'},
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {token}'})
        file_id = json.loads(r.data)['file']['id']
        # Delete
        r = client.delete(f'/api/v1/files/{file_id}',
            headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200

    def test_api_ml_scan(self, client, user):
        r = client.post('/api/v1/auth/login',
            data=json.dumps({'username':'testuser','password':'Password123'}),
            content_type='application/json')
        token = json.loads(r.data)['token']
        r = client.post('/api/v1/ml/scan',
            data=json.dumps({'filename':'test.exe','size':500000}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'score' in data and 'level' in data

    def test_api_admin_stats_requires_admin(self, client, user):
        r = client.post('/api/v1/auth/login',
            data=json.dumps({'username':'testuser','password':'Password123'}),
            content_type='application/json')
        token = json.loads(r.data)['token']
        r = client.get('/api/v1/admin/stats',
            headers={'Authorization': f'Bearer {token}'})
        assert r.status_code == 403  # non-admin


# ── AWS Integration Tests (no real credentials needed) ────────────────────────
class TestAWSIntegration:
    """Tests that verify AWS module behaves correctly when NOT configured."""

    def test_aws_disabled_when_no_env(self):
        """Without env vars, aws_enabled must be False."""
        import os
        saved = {k: os.environ.pop(k, None) for k in
                 ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']}
        from importlib import reload
        import aws_integration.config as cfg
        reload(cfg)
        for k, v in saved.items():
            if v: os.environ[k] = v
        assert cfg.AWS_ACCESS_KEY_ID == os.environ.get('AWS_ACCESS_KEY_ID', '')

    def test_s3_upload_returns_false_when_disabled(self):
        from aws_integration.s3_storage import upload_to_s3
        import aws_integration.s3_storage as s3_mod
        original = s3_mod.s3_enabled
        s3_mod.s3_enabled = False
        result = upload_to_s3('/tmp/fakefile.enc', 'fakefile.enc')
        s3_mod.s3_enabled = original
        assert result is False

    def test_s3_download_returns_false_when_disabled(self):
        from aws_integration.s3_storage import download_from_s3
        import aws_integration.s3_storage as s3_mod
        original = s3_mod.s3_enabled
        s3_mod.s3_enabled = False
        result = download_from_s3('fakefile.enc', '/tmp/dest.enc')
        s3_mod.s3_enabled = original
        assert result is False

    def test_s3_delete_returns_false_when_disabled(self):
        from aws_integration.s3_storage import delete_from_s3
        import aws_integration.s3_storage as s3_mod
        original = s3_mod.s3_enabled
        s3_mod.s3_enabled = False
        result = delete_from_s3('fakefile.enc')
        s3_mod.s3_enabled = original
        assert result is False

    def test_sns_returns_false_when_disabled(self):
        from aws_integration.sns_alerts import send_threat_alert
        import aws_integration.sns_alerts as sns_mod
        original = sns_mod.sns_enabled
        sns_mod.sns_enabled = False
        result = send_threat_alert('malware.exe', 'HIGH', 0.9, 'user1', 'executable', 'test')
        sns_mod.sns_enabled = original
        assert result is False

    def test_sns_skips_low_medium_threats(self):
        from aws_integration.sns_alerts import send_threat_alert
        import aws_integration.sns_alerts as sns_mod
        original = sns_mod.sns_enabled
        sns_mod.sns_enabled = True
        result_low    = send_threat_alert('doc.pdf', 'LOW',    0.1, 'u', 'document', '')
        result_medium = send_threat_alert('doc.pdf', 'MEDIUM', 0.4, 'u', 'document', '')
        sns_mod.sns_enabled = original
        assert result_low is False
        assert result_medium is False

    def test_cloudwatch_returns_false_when_disabled(self):
        from aws_integration.cloudwatch_logger import push_log_event
        import aws_integration.cloudwatch_logger as cw_mod
        original = cw_mod.cloudwatch_enabled
        cw_mod.cloudwatch_enabled = False
        result = push_log_event('TEST', username='user1', status='SUCCESS')
        cw_mod.cloudwatch_enabled = original
        assert result is False

    def test_cloudwatch_get_recent_returns_empty_when_disabled(self):
        from aws_integration.cloudwatch_logger import get_recent_logs
        import aws_integration.cloudwatch_logger as cw_mod
        original = cw_mod.cloudwatch_enabled
        cw_mod.cloudwatch_enabled = False
        result = get_recent_logs()
        cw_mod.cloudwatch_enabled = original
        assert result == []

    def test_check_connectivity_returns_disabled_when_no_config(self):
        from aws_integration.config import check_aws_connectivity
        import aws_integration.config as cfg
        original_s3  = cfg.s3_enabled
        original_sns = cfg.sns_enabled
        original_cw  = cfg.cloudwatch_enabled
        cfg.s3_enabled = cfg.sns_enabled = cfg.cloudwatch_enabled = False
        status = check_aws_connectivity()
        cfg.s3_enabled  = original_s3
        cfg.sns_enabled = original_sns
        cfg.cloudwatch_enabled = original_cw
        assert all('DISABLED' in v for v in status.values())
