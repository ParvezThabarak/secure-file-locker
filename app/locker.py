import os, uuid, mimetypes
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, send_file, abort, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import LockedFile, User
from app.crypto_utils import encrypt_file, decrypt_file, get_file_hash
from app.audit import log_event
from ml_engine import compute_threat_score
from aws_integration.s3_storage import upload_to_s3, download_from_s3, delete_from_s3
from aws_integration.sns_alerts import send_threat_alert
from app.notifications import emit_admin_alert

locker = Blueprint('locker', __name__)

ALLOWED_EXT = {
    'txt','pdf','png','jpg','jpeg','gif','docx','xlsx','pptx',
    'zip','mp4','mp3','csv','py','js','html','md','tar','gz'
}


def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@locker.route('/dashboard')
@login_required
def dashboard():
    q     = request.args.get('q', '').strip()
    tag   = request.args.get('tag', '').strip()
    sort  = request.args.get('sort', 'recent')

    query = LockedFile.query.filter_by(user_id=current_user.id, parent_id=None)

    if q:
        query = query.filter(LockedFile.original_filename.ilike(f'%{q}%'))
    if tag:
        query = query.filter(LockedFile.tags.ilike(f'%{tag}%'))

    if sort == 'name':
        query = query.order_by(LockedFile.original_filename.asc())
    elif sort == 'size':
        query = query.order_by(LockedFile.file_size.desc())
    elif sort == 'threat':
        query = query.order_by(LockedFile.ml_threat_score.desc())
    else:
        query = query.order_by(LockedFile.upload_time.desc())

    files      = query.all()
    total_size = sum(f.file_size for f in files)
    threat_files = [f for f in files if f.ml_threat_score > 0.6]

    return render_template('dashboard.html', files=files, total_size=total_size,
                           threat_files=threat_files, q=q, tag=tag, sort=sort)


@locker.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file        = request.files.get('file')
        password    = request.form.get('password', '').strip()
        description = request.form.get('description', '').strip()
        tags        = request.form.get('tags', '').strip()
        parent_id   = request.form.get('parent_id', type=int)

        if not file or not file.filename:
            flash('No file selected.', 'danger'); return redirect(url_for('locker.upload'))
        if not allowed(file.filename):
            flash('File type not allowed.', 'danger'); return redirect(url_for('locker.upload'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger'); return redirect(url_for('locker.upload'))

        # Check quota
        if current_user.storage_used >= current_user.storage_quota:
            flash('Storage quota exceeded. Delete some files first.', 'danger')
            return redirect(url_for('locker.dashboard'))

        original_filename = secure_filename(file.filename)
        uid           = str(uuid.uuid4())
        stored_name   = f"{uid}.enc"
        upload_folder = current_app.config['UPLOAD_FOLDER']
        temp_path     = os.path.join(upload_folder, f"{uid}_tmp")
        enc_path      = os.path.join(upload_folder, stored_name)

        try:
            file.save(temp_path)
            file_size = os.path.getsize(temp_path)
            file_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
            ext       = os.path.splitext(original_filename)[1].lower()

            # ── ML Analysis ──────────────────────────────────────────────
            is_new_user  = current_user.login_count <= 2
            ml_result    = compute_threat_score(
                original_filename, file_size,
                user_failed_logins=current_user.failed_logins,
                is_new_user=is_new_user
            )

            encrypt_file(temp_path, enc_path, password)

            version = 1
            if parent_id:
                parent = LockedFile.query.filter_by(id=parent_id, user_id=current_user.id).first()
                if parent:
                    version = parent.version + 1

            lf = LockedFile(
                original_filename = original_filename,
                stored_filename   = stored_name,
                file_size         = file_size,
                file_type         = file_type,
                file_extension    = ext,
                encrypted         = True,
                user_id           = current_user.id,
                description       = description,
                tags              = tags,
                version           = version,
                parent_id         = parent_id,
                ml_file_category  = ml_result['category'],
                ml_threat_score   = ml_result['score'],
                ml_is_anomaly     = ml_result['is_anomaly'],
                ml_confidence     = ml_result['confidence'],
            )
            db.session.add(lf)
            current_user.storage_used += file_size
            db.session.commit()

            # ── AWS: upload encrypted file to S3 (optional) ──────────────
            upload_to_s3(enc_path, stored_name)

            status = 'BLOCKED' if ml_result['level'] == 'CRITICAL' else 'SUCCESS'
            log_event('UPLOAD', resource=original_filename, status=status,
                      threat_score=ml_result['score'],
                      details=f"category={ml_result['category']} threat={ml_result['level']}")

            # ── AWS: SNS alert for HIGH/CRITICAL threats (optional) ───────
            send_threat_alert(
                filename=original_filename,
                threat_level=ml_result['level'],
                threat_score=ml_result['score'],
                username=current_user.username,
                category=ml_result['category'],
                anomaly_reason=ml_result['anomaly_reason'],
                user_ip=request.remote_addr
            )

            if ml_result['level'] in ('HIGH', 'CRITICAL'):
                flash(f'⚠️ High-risk file detected! Threat score: {ml_result["score"]:.2f} — Reason: {ml_result["anomaly_reason"]}', 'warning')
                emit_admin_alert(
                    f'🚨 High-risk upload: {original_filename} by {current_user.username} '
                    f'(threat={ml_result["score"]:.2f}, level={ml_result["level"]})')
            else:
                flash(f'"{original_filename}" encrypted and locked. ML category: {ml_result["category"].upper()}', 'success')

        except Exception as e:
            flash(f'Upload failed: {e}', 'danger')
            log_event('UPLOAD', resource=original_filename, status='FAILURE', details=str(e))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return redirect(url_for('locker.dashboard'))
    return render_template('upload.html')


@locker.route('/download/<int:file_id>', methods=['GET', 'POST'])
@login_required
def download(file_id):
    lf = LockedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        password      = request.form.get('password', '').strip()
        upload_folder = current_app.config['UPLOAD_FOLDER']
        enc_path      = os.path.join(upload_folder, lf.stored_filename)
        dec_path      = os.path.join(upload_folder, f"dec_{lf.stored_filename}")

        try:
            # Try local disk first; fall back to S3 if not found locally
            if not os.path.exists(enc_path):
                download_from_s3(lf.stored_filename, enc_path)
            decrypt_file(enc_path, dec_path, password)
            lf.download_count += 1
            db.session.commit()
            log_event('DOWNLOAD', resource=lf.original_filename, status='SUCCESS')
            return send_file(dec_path, as_attachment=True,
                             download_name=lf.original_filename, mimetype=lf.file_type)
        except Exception:
            if os.path.exists(dec_path): os.remove(dec_path)
            flash('Decryption failed. Wrong password?', 'danger')
            log_event('DOWNLOAD', resource=lf.original_filename, status='FAILURE')
    return render_template('download.html', file=lf)


@locker.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    lf = LockedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    upload_folder = current_app.config['UPLOAD_FOLDER']
    enc_path      = os.path.join(upload_folder, lf.stored_filename)
    try:
        if os.path.exists(enc_path): os.remove(enc_path)
        delete_from_s3(lf.stored_filename)   # no-op if S3 disabled
        current_user.storage_used = max(0, current_user.storage_used - lf.file_size)
        name = lf.original_filename
        db.session.delete(lf)
        db.session.commit()
        log_event('DELETE', resource=name, status='SUCCESS')
        flash(f'"{name}" permanently deleted.', 'success')
    except Exception as e:
        flash(f'Delete failed: {e}', 'danger')
    return redirect(url_for('locker.dashboard'))


@locker.route('/file/<int:file_id>')
@login_required
def file_detail(file_id):
    lf = LockedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    versions = LockedFile.query.filter_by(parent_id=lf.parent_id or lf.id, user_id=current_user.id).all() if lf.parent_id or lf.versions else []
    return render_template('file_detail.html', file=lf, versions=versions)


@locker.route('/api/ml-scan', methods=['POST'])
@login_required
def ml_scan():
    """API endpoint: real-time ML scan before upload."""
    data     = request.get_json()
    filename = data.get('filename', '')
    size     = int(data.get('size', 0))
    result   = compute_threat_score(filename, size,
                                     user_failed_logins=current_user.failed_logins)
    return jsonify(result)
