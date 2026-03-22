"""
Analytics Routes — ML anomaly detection results + access logs
Satisfies PBL-II: Data / ML / AI Workflow (4 marks)
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.access_log import AccessLog
from services.ml_service import get_user_risk_summary
from app.database.database import db
from datetime import datetime, timedelta
import logging
import json

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)


@analytics_bp.route('/risk-summary', methods=['GET'])
@login_required
def risk_summary():
    """Get ML risk summary for the current user — last 24 hours."""
    try:
        summary = get_user_risk_summary(current_user.id)
        return jsonify(summary), 200
    except Exception as e:
        logger.error(f"Error getting risk summary: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/access-logs', methods=['GET'])
@login_required
def access_logs():
    """Get recent access logs for current user — used by Kibana dashboard."""
    try:
        hours = int(request.args.get('hours', 24))
        since = datetime.utcnow() - timedelta(hours=hours)
        logs = AccessLog.query.filter_by(user_id=current_user.id)\
            .filter(AccessLog.timestamp >= since)\
            .order_by(AccessLog.timestamp.desc())\
            .limit(100).all()

        return jsonify({
            'logs': [l.to_dict() for l in logs],
            'total': len(logs),
            'period_hours': hours
        }), 200
    except Exception as e:
        logger.error(f"Error getting access logs: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/high-risk-events', methods=['GET'])
@login_required
def high_risk_events():
    """Get all HIGH risk events for current user — security alert feed."""
    try:
        since = datetime.utcnow() - timedelta(hours=24)
        events = AccessLog.query.filter_by(
            user_id=current_user.id,
            risk_level='HIGH'
        ).filter(AccessLog.timestamp >= since)\
         .order_by(AccessLog.timestamp.desc()).all()

        return jsonify({
            'high_risk_events': [e.to_dict() for e in events],
            'count': len(events)
        }), 200
    except Exception as e:
        logger.error(f"Error getting high risk events: {e}")
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/stats', methods=['GET'])
@login_required
def action_stats():
    """Get action statistics for charts — uploads, downloads, deletes per day."""
    try:
        since = datetime.utcnow() - timedelta(days=7)
        logs = AccessLog.query.filter_by(user_id=current_user.id)\
            .filter(AccessLog.timestamp >= since).all()

        stats = {'upload': 0, 'download': 0, 'delete': 0, 'share': 0, 'login': 0}
        for log in logs:
            if log.action in stats:
                stats[log.action] += 1

        return jsonify({
            'stats': stats,
            'period': '7 days',
            'total_events': len(logs)
        }), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500
