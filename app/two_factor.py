"""
Two-Factor Authentication (TOTP) Blueprint
============================================
Provides setup, enable, verify, and disable routes for Google Authenticator
compatible TOTP-based two-factor authentication.
"""
import io, base64
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user, login_user
from app import db
from app.models import User
from app.audit import log_event

twofa = Blueprint('twofa', __name__, url_prefix='/2fa')


@twofa.route('/setup')
@login_required
def setup():
    """Display QR code for Google Authenticator setup."""
    if current_user.totp_enabled:
        flash('2FA is already enabled on your account.', 'info')
        return redirect(url_for('locker.dashboard'))

    # Generate TOTP secret only if one doesn't exist yet
    if not current_user.totp_secret:
        current_user.generate_totp_secret()
        db.session.commit()

    # Generate QR code as base64 PNG
    import pyotp
    import qrcode
    from qrcode.image.pil import PilImage

    totp_uri = current_user.get_totp_uri()
    qr = qrcode.QRCode(version=1, box_size=6, border=2,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color='white', back_color='#0a0e1a', image_factory=PilImage)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('2fa_setup.html',
                           qr_data=qr_b64,
                           secret=current_user.totp_secret)


@twofa.route('/enable', methods=['POST'])
@login_required
def enable():
    """Verify the first TOTP code and enable 2FA."""
    code = request.form.get('code', '').replace(' ', '').strip()
    if not code:
        flash('Please enter the 6-digit code from your authenticator app.', 'danger')
        return redirect(url_for('twofa.setup'))

    if current_user.verify_totp(code):
        current_user.totp_enabled = True
        db.session.commit()
        log_event('2FA_ENABLE', status='SUCCESS')
        flash('✅ Two-Factor Authentication has been enabled!', 'success')
        return redirect(url_for('locker.dashboard'))
    else:
        flash('Invalid code. Please try again — make sure your clock is synced.', 'danger')
        return redirect(url_for('twofa.setup'))


@twofa.route('/verify', methods=['GET', 'POST'])
def verify():
    """Intermediate 2FA verification step during login."""
    pending_user_id = session.get('pending_2fa_user_id')
    if not pending_user_id:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').replace(' ', '').strip()
        user = User.query.get(pending_user_id)

        if user and user.verify_totp(code):
            session.pop('pending_2fa_user_id', None)
            remember = session.pop('pending_2fa_remember', False)
            login_user(user, remember=remember)
            log_event('LOGIN', resource=user.username, status='SUCCESS',
                      details='2FA verified')
            return redirect(request.args.get('next') or url_for('locker.dashboard'))
        else:
            flash('Invalid 2FA code. Please try again.', 'danger')
            log_event('LOGIN', resource=user.username if user else 'unknown',
                      status='FAILURE', details='2FA code rejected')

    return render_template('2fa_verify.html')


@twofa.route('/disable', methods=['POST'])
@login_required
def disable():
    """Disable 2FA after verifying current TOTP code."""
    code = request.form.get('code', '').replace(' ', '').strip()
    if current_user.verify_totp(code):
        current_user.totp_enabled = False
        current_user.totp_secret = None
        db.session.commit()
        log_event('2FA_DISABLE', status='SUCCESS')
        flash('Two-Factor Authentication has been disabled.', 'info')
    else:
        flash('Invalid code. 2FA was NOT disabled.', 'danger')
    return redirect(url_for('locker.dashboard'))
