from flask import request
from app import db
from app.models import AuditLog
from flask_login import current_user


def log_event(action: str, resource: str = None, status: str = 'SUCCESS',
              details: str = None, threat_score: float = 0.0, user_id: int = None):
    """Write an audit log entry to local DB and optionally to CloudWatch."""
    try:
        uid = user_id
        uname = None
        if uid is None and current_user and current_user.is_authenticated:
            uid = current_user.id
            uname = current_user.username

        ip = request.remote_addr if request else None

        entry = AuditLog(
            user_id      = uid,
            action       = action,
            resource     = resource,
            ip_address   = ip,
            user_agent   = (request.user_agent.string[:256] if request and request.user_agent else None),
            status       = status,
            details      = details,
            threat_score = threat_score
        )
        db.session.add(entry)
        db.session.commit()

        # ── AWS CloudWatch (optional, non-blocking) ───────────────────────
        try:
            from aws_integration.cloudwatch_logger import push_log_event
            push_log_event(
                action=action, user_id=uid, username=uname,
                resource=resource, status=status,
                threat_score=threat_score, ip_address=ip, details=details
            )
        except Exception:
            pass   # CloudWatch failure must never affect main flow

    except Exception as e:
        print(f"[Audit] Logging failed (non-critical): {e}")
