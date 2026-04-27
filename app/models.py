from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin      = db.Column(db.Boolean, default=False)
    is_active_acc = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.now)
    last_login    = db.Column(db.DateTime)
    login_count   = db.Column(db.Integer, default=0)
    failed_logins = db.Column(db.Integer, default=0)
    storage_used  = db.Column(db.BigInteger, default=0)   # bytes
    storage_quota = db.Column(db.BigInteger, default=500 * 1024 * 1024)  # 500 MB

    # ── Email Verification (on suspicious login) ──────────────────────────
    email_verify_code    = db.Column(db.String(6), nullable=True)
    email_verify_expires = db.Column(db.DateTime, nullable=True)

    files     = db.relationship('LockedFile', backref='owner', lazy=True, cascade='all, delete-orphan', foreign_keys='LockedFile.user_id')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def storage_percent(self):
        return min(100, int((self.storage_used / self.storage_quota) * 100))

    def generate_verify_code(self):
        """Generate a 6-digit email verification code valid for 10 minutes."""
        import random
        from datetime import timedelta
        self.email_verify_code = f"{random.randint(100000, 999999)}"
        self.email_verify_expires = datetime.now() + timedelta(minutes=10)
        return self.email_verify_code

    def check_verify_code(self, code):
        """Verify the email code and check expiry."""
        if not self.email_verify_code or not self.email_verify_expires:
            return False
        if datetime.now() > self.email_verify_expires:
            return False
        return self.email_verify_code == code.strip()

    def __repr__(self):
        return f'<User {self.username}>'


class LockedFile(db.Model):
    __tablename__ = 'locked_files'
    id                = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(256), nullable=False)
    stored_filename   = db.Column(db.String(256), nullable=False, unique=True)
    file_size         = db.Column(db.BigInteger, nullable=False)
    file_type         = db.Column(db.String(64))
    file_extension    = db.Column(db.String(16))
    encrypted         = db.Column(db.Boolean, default=True)
    upload_time       = db.Column(db.DateTime, default=datetime.now)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    download_count    = db.Column(db.Integer, default=0)
    description       = db.Column(db.String(512))
    tags              = db.Column(db.String(256))        # comma-separated

    # ML predictions
    ml_file_category  = db.Column(db.String(64))         # Random Forest classifier label
    ml_threat_score   = db.Column(db.Float, default=0.0) # 0.0 – 1.0 risk score
    ml_is_anomaly     = db.Column(db.Boolean, default=False)
    ml_confidence     = db.Column(db.Float, default=0.0)

    # Versioning
    version           = db.Column(db.Integer, default=1)
    parent_id         = db.Column(db.Integer, db.ForeignKey('locked_files.id'), nullable=True)
    versions          = db.relationship('LockedFile', backref=db.backref('parent', remote_side=[id]))

    shares            = db.relationship('SharedFile', backref='file', lazy=True, cascade='all, delete-orphan')

    def threat_label(self):
        if self.ml_threat_score < 0.3:
            return 'LOW', 'green'
        elif self.ml_threat_score < 0.7:
            return 'MEDIUM', 'orange'
        return 'HIGH', 'red'

    def __repr__(self):
        return f'<LockedFile {self.original_filename} v{self.version}>'


class SharedFile(db.Model):
    __tablename__ = 'shared_files'
    id           = db.Column(db.Integer, primary_key=True)
    file_id      = db.Column(db.Integer, db.ForeignKey('locked_files.id'), nullable=False)
    shared_by    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_with  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # None = public link
    token        = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    expires_at   = db.Column(db.DateTime, nullable=True)
    max_downloads= db.Column(db.Integer, default=5)
    download_count = db.Column(db.Integer, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.now)
    is_active    = db.Column(db.Boolean, default=True)

    sharer       = db.relationship('User', foreign_keys=[shared_by])
    recipient    = db.relationship('User', foreign_keys=[shared_with])

    def is_valid(self):
        if not self.is_active:
            return False, "Link has been revoked"
        if self.expires_at and datetime.now() > self.expires_at:
            return False, "Link has expired"
        if self.download_count >= self.max_downloads:
            return False, "Download limit reached"
        return True, "OK"


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action     = db.Column(db.String(64), nullable=False)   # LOGIN, UPLOAD, DOWNLOAD, DELETE, SHARE, etc.
    resource   = db.Column(db.String(256))                  # filename or URL
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    status     = db.Column(db.String(16), default='SUCCESS') # SUCCESS / FAILURE / BLOCKED
    details    = db.Column(db.Text)
    threat_score = db.Column(db.Float, default=0.0)
    timestamp  = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'
