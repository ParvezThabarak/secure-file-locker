from datetime import datetime
from app.database.database import db
from cryptography.fernet import Fernet
import os
import base64

class AWSCredentials(db.Model):
    __tablename__ = 'aws_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Encrypted AWS credentials
    access_key_id_encrypted = db.Column(db.Text, nullable=False)
    secret_access_key_encrypted = db.Column(db.Text, nullable=False)
    region = db.Column(db.String(50), nullable=False, default='us-east-1')
    bucket_name = db.Column(db.String(255), nullable=False)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('aws_credentials', uselist=False))
    
    def __repr__(self):
        return f'<AWSCredentials {self.user_id}>'
    
    @staticmethod
    def _get_encryption_key():
        """Get or create encryption key for AWS credentials"""
        key = os.getenv('AWS_CREDENTIALS_ENCRYPTION_KEY')
        if not key:
            # Generate a new key if none exists (for development)
            key = Fernet.generate_key()
            print(f"WARNING: Generated new encryption key. Set AWS_CREDENTIALS_ENCRYPTION_KEY={key.decode()} in your .env file")
        else:
            key = key.encode()
        return key
    
    def set_credentials(self, access_key_id, secret_access_key, region, bucket_name):
        """Encrypt and store AWS credentials"""
        key = self._get_encryption_key()
        f = Fernet(key)
        
        self.access_key_id_encrypted = f.encrypt(access_key_id.encode()).decode()
        self.secret_access_key_encrypted = f.encrypt(secret_access_key.encode()).decode()
        self.region = region
        self.bucket_name = bucket_name
        self.is_active = True
    
    def get_credentials(self):
        """Decrypt and return AWS credentials"""
        if not self.is_active:
            return None
            
        key = self._get_encryption_key()
        f = Fernet(key)
        
        try:
            access_key_id = f.decrypt(self.access_key_id_encrypted.encode()).decode()
            secret_access_key = f.decrypt(self.secret_access_key_encrypted.encode()).decode()
            
            return {
                'access_key_id': access_key_id,
                'secret_access_key': secret_access_key,
                'region': self.region,
                'bucket_name': self.bucket_name
            }
        except Exception as e:
            print(f"Error decrypting AWS credentials: {e}")
            return None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization (without sensitive data)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'region': self.region,
            'bucket_name': self.bucket_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
