from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pyotp
import secrets
import json
from app.database.database import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_2fa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    otp_secret = db.Column(db.String(32), nullable=True)
    recovery_codes = db.Column(db.Text, nullable=True)  # JSON array of recovery codes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship with files
    files = db.relationship('File', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)
    
    def generate_otp_secret(self):
        """Generate a new OTP secret for 2FA"""
        self.otp_secret = pyotp.random_base32()
        return self.otp_secret
    
    def get_otp_uri(self):
        """Get the OTP URI for QR code generation"""
        if not self.otp_secret:
            return None
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.email,
            issuer_name="S3 File Manager"
        )
    
    def verify_otp(self, token):
        """Verify the provided OTP token"""
        if not self.otp_secret:
            return False
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(token, valid_window=1)
    
    def enable_2fa(self):
        """Enable 2FA for the user"""
        if not self.otp_secret:
            self.generate_otp_secret()
        self.is_2fa_enabled = True
    
    def disable_2fa(self):
        """Disable 2FA for the user"""
        self.is_2fa_enabled = False
        self.otp_secret = None
        self.recovery_codes = None
    
    def generate_recovery_codes(self, count=10):
        """Generate recovery codes for 2FA backup"""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            codes.append(code)
        
        # Store as JSON string
        self.recovery_codes = json.dumps(codes)
        return codes
    
    def get_recovery_codes(self):
        """Get the list of recovery codes"""
        if not self.recovery_codes:
            return []
        try:
            return json.loads(self.recovery_codes)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def verify_recovery_code(self, code):
        """Verify a recovery code and remove it if valid"""
        codes = self.get_recovery_codes()
        if code.upper() in codes:
            # Remove the used code
            codes.remove(code.upper())
            if codes:
                self.recovery_codes = json.dumps(codes)
            else:
                self.recovery_codes = None
            return True
        return False
    
    def has_recovery_codes(self):
        """Check if user has any unused recovery codes"""
        return len(self.get_recovery_codes()) > 0
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_2fa_enabled': self.is_2fa_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
