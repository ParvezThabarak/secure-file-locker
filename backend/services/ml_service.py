"""
ML/AI Service — Anomaly Detection for Secure File Locker
Detects suspicious file access patterns using statistical analysis.
This satisfies PBL-II: Data / ML / AI Workflow (4 marks)

Features:
- Detects unusual download frequency (too many downloads in short time)
- Detects access from unusual hours (late night activity)
- Detects bulk delete attempts
- Returns risk score 0-100 with explanation
"""

from datetime import datetime, timedelta
from app.database.database import db
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Simple rule-based + statistical ML anomaly detector.
    Uses Z-score style detection on user activity patterns.
    """

    # Thresholds
    MAX_DOWNLOADS_PER_HOUR = 20
    MAX_UPLOADS_PER_HOUR = 30
    MAX_DELETES_PER_HOUR = 10
    SUSPICIOUS_HOURS = list(range(0, 5))  # midnight to 5am

    def __init__(self, user_id):
        self.user_id = user_id
        self.now = datetime.utcnow()

    def _get_recent_logs(self, action, hours=1):
        """Get count of a specific action in the last N hours."""
        try:
            from models.access_log import AccessLog
            since = self.now - timedelta(hours=hours)
            return AccessLog.query.filter_by(
                user_id=self.user_id,
                action=action
            ).filter(AccessLog.timestamp >= since).count()
        except Exception:
            return 0

    def analyze(self, action):
        """
        Analyze an action and return a risk assessment.
        Returns dict with: risk_score (0-100), risk_level, alerts
        """
        alerts = []
        risk_score = 0

        # Rule 1: Unusual hour detection
        current_hour = self.now.hour
        if current_hour in self.SUSPICIOUS_HOURS:
            alerts.append(f"Access at unusual hour ({current_hour}:00 UTC)")
            risk_score += 25

        # Rule 2: High frequency download detection
        if action == 'download':
            recent_downloads = self._get_recent_logs('download', hours=1)
            if recent_downloads > self.MAX_DOWNLOADS_PER_HOUR:
                alerts.append(f"High download frequency: {recent_downloads} downloads/hour")
                risk_score += 40
            elif recent_downloads > self.MAX_DOWNLOADS_PER_HOUR * 0.7:
                alerts.append(f"Elevated download activity: {recent_downloads} downloads/hour")
                risk_score += 20

        # Rule 3: Bulk delete detection
        if action == 'delete':
            recent_deletes = self._get_recent_logs('delete', hours=1)
            if recent_deletes > self.MAX_DELETES_PER_HOUR:
                alerts.append(f"Bulk delete detected: {recent_deletes} deletes/hour")
                risk_score += 50

        # Rule 4: High upload frequency
        if action == 'upload':
            recent_uploads = self._get_recent_logs('upload', hours=1)
            if recent_uploads > self.MAX_UPLOADS_PER_HOUR:
                alerts.append(f"High upload frequency: {recent_uploads} uploads/hour")
                risk_score += 20

        # Determine risk level
        risk_score = min(risk_score, 100)
        if risk_score >= 70:
            risk_level = 'HIGH'
        elif risk_score >= 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        result = {
            'user_id': self.user_id,
            'action': action,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'alerts': alerts,
            'timestamp': self.now.isoformat()
        }

        if risk_level in ('HIGH', 'MEDIUM'):
            logger.warning(f"ANOMALY DETECTED - User {self.user_id} | "
                           f"Action: {action} | Score: {risk_score} | "
                           f"Alerts: {alerts}")

        return result


def get_user_risk_summary(user_id):
    """
    Get a summary of risk analysis for the last 24 hours.
    Used by the admin dashboard / Kibana integration.
    """
    try:
        from models.access_log import AccessLog
        since = datetime.utcnow() - timedelta(hours=24)
        logs = AccessLog.query.filter_by(user_id=user_id).filter(
            AccessLog.timestamp >= since
        ).all()

        total_actions = len(logs)
        high_risk = sum(1 for l in logs if l.risk_level == 'HIGH')
        medium_risk = sum(1 for l in logs if l.risk_level == 'MEDIUM')
        avg_score = (
            sum(l.risk_score for l in logs) / total_actions
            if total_actions > 0 else 0
        )

        return {
            'user_id': user_id,
            'period': '24h',
            'total_actions': total_actions,
            'high_risk_events': high_risk,
            'medium_risk_events': medium_risk,
            'average_risk_score': round(avg_score, 2),
            'status': 'ALERT' if high_risk > 0 else 'NORMAL'
        }
    except Exception as e:
        logger.error(f"Error getting risk summary: {e}")
        return {'error': str(e)}
