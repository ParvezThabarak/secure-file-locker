from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models import SharedFile, LockedFile, User
from app.crypto_utils import decrypt_file
from app.audit import log_event
from datetime import datetime, timedelta
import os

sharing = Blueprint('sharing', __name__)

from app.notifications import emit_notification


@sharing.route('/create/<int:file_id>', methods=['POST'])
@login_required
def create_share(file_id):
    lf = LockedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()

    expires_hours  = int(request.form.get('expires_hours', 24))
    max_downloads  = int(request.form.get('max_downloads', 5))
    shared_with_un = request.form.get('shared_with', '').strip()

    recipient = None
    if shared_with_un:
        recipient = User.query.filter_by(username=shared_with_un).first()
        if not recipient:
            flash(f'User "{shared_with_un}" not found.', 'danger')
            return redirect(url_for('locker.file_detail', file_id=file_id))

    share = SharedFile(
        file_id       = file_id,
        shared_by     = current_user.id,
        shared_with   = recipient.id if recipient else None,
        expires_at    = datetime.now() + timedelta(hours=expires_hours),
        max_downloads = max_downloads,
    )
    db.session.add(share)
    db.session.commit()

    log_event('SHARE', resource=lf.original_filename,
              details=f"token={share.token} expires={expires_hours}h")

    share_url = url_for('sharing.access_share', token=share.token, _external=True)
    flash(f'Share link created: {share_url}', 'success')

    # ── Real-time notification to recipient ───────────────────────────────
    if recipient:
        emit_notification(recipient.id,
            f'📎 {current_user.username} shared "{lf.original_filename}" with you',
            notif_type='info', icon='🔗')

    return redirect(url_for('locker.file_detail', file_id=file_id))


@sharing.route('/<token>', methods=['GET', 'POST'])
def access_share(token):
    share = SharedFile.query.filter_by(token=token).first_or_404()
    valid, msg = share.is_valid()
    if not valid:
        abort(410, description=msg)

    lf = share.file
    if request.method == 'POST':
        password      = request.form.get('password', '').strip()
        upload_folder = current_app.config['UPLOAD_FOLDER']
        enc_path      = os.path.join(upload_folder, lf.stored_filename)
        dec_path      = os.path.join(upload_folder, f"shared_dec_{share.token}")
        try:
            decrypt_file(enc_path, dec_path, password)
            share.download_count += 1
            db.session.commit()
            log_event('SHARE_DOWNLOAD', resource=lf.original_filename,
                      status='SUCCESS', details=f"token={token}")
            return send_file(dec_path, as_attachment=True,
                             download_name=lf.original_filename, mimetype=lf.file_type)
        except Exception:
            if os.path.exists(dec_path): os.remove(dec_path)
            flash('Wrong decryption password.', 'danger')

    return render_template('share_access.html', share=share, file=lf)


@sharing.route('/revoke/<int:share_id>', methods=['POST'])
@login_required
def revoke(share_id):
    share = SharedFile.query.filter_by(id=share_id, shared_by=current_user.id).first_or_404()
    share.is_active = False
    db.session.commit()
    log_event('SHARE_REVOKE', resource=str(share.file_id))
    flash('Share link revoked.', 'success')
    return redirect(url_for('locker.file_detail', file_id=share.file_id))
