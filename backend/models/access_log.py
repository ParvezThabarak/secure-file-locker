"""
AccessLog Model — tracks all user file actions for ML anomaly detection
and ELK Stack / Kibana dashboard integration.
"""
from datetime import datetime
from app.database.database import db


class AccessLog(db.Model):
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)       # upload, download, delete, share, login
    filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.BigInteger, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    risk_score = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(10), default='LOW')    # LOW, MEDIUM, HIGH
    alerts = db.Column(db.Text, nullable=True)              # JSON alerts from ML
    status = db.Column(db.String(20), default='success')    # success, failed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'filename': self.filename,
            'file_size': self.file_size,
            'ip_address': self.ip_address,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'alerts': self.alerts,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
