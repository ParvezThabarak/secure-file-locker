from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, LockedFile, AuditLog, SharedFile
from ml_engine import get_ml_stats
from aws_integration.config import check_aws_connectivity, aws_enabled, s3_enabled, sns_enabled, cloudwatch_enabled
from aws_integration.cloudwatch_logger import get_recent_logs
from sqlalchemy import func

admin = Blueprint('admin', __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin.route('/')
@login_required
@admin_required
def dashboard():
    total_users  = User.query.count()
    total_files  = LockedFile.query.count()
    total_size   = db.session.query(func.sum(LockedFile.file_size)).scalar() or 0
    high_threats = LockedFile.query.filter(LockedFile.ml_threat_score > 0.6).count()
    anomalies    = LockedFile.query.filter_by(ml_is_anomaly=True).count()
    recent_logs  = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(20).all()
    ml_stats     = get_ml_stats()
    aws_status   = check_aws_connectivity()
    cloud_logs   = get_recent_logs(limit=10)

    # Category breakdown
    cat_data = db.session.query(
        LockedFile.ml_file_category, func.count(LockedFile.id)
    ).group_by(LockedFile.ml_file_category).all()

    # Threat level breakdown
    threat_data = {
        'LOW':      LockedFile.query.filter(LockedFile.ml_threat_score < 0.3).count(),
        'MEDIUM':   LockedFile.query.filter(LockedFile.ml_threat_score.between(0.3, 0.6)).count(),
        'HIGH':     LockedFile.query.filter(LockedFile.ml_threat_score.between(0.6, 0.8)).count(),
        'CRITICAL': LockedFile.query.filter(LockedFile.ml_threat_score >= 0.8).count(),
    }

    return render_template('admin/dashboard.html',
        total_users=total_users, total_files=total_files,
        total_size=total_size, high_threats=high_threats,
        anomalies=anomalies, recent_logs=recent_logs,
        ml_stats=ml_stats, cat_data=cat_data, threat_data=threat_data,
        aws_status=aws_status, cloud_logs=cloud_logs,
        aws_enabled=aws_enabled, s3_enabled=s3_enabled,
        sns_enabled=sns_enabled, cloudwatch_enabled=cloudwatch_enabled)


@admin.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Cannot deactivate admin accounts.", 'danger')
    else:
        user.is_active_acc = not user.is_active_acc
        user.failed_logins = 0
        db.session.commit()
        flash(f'User "{user.username}" {"activated" if user.is_active_acc else "deactivated"}.', 'success')
    return redirect(url_for('admin.users'))


@admin.route('/threats')
@login_required
@admin_required
def threats():
    flagged = LockedFile.query.filter(LockedFile.ml_threat_score > 0.5)\
                .order_by(LockedFile.ml_threat_score.desc()).all()
    return render_template('admin/threats.html', flagged=flagged)


@admin.route('/audit')
@login_required
@admin_required
def audit():
    page  = request.args.get('page', 1, type=int)
    logs  = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=50)
    return render_template('admin/audit.html', logs=logs)
