from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.audit import log_event
from datetime import datetime

auth = Blueprint('auth', __name__)

MAX_FAILED = 5       # lock account after 5 failures
VERIFY_THRESHOLD = 3 # require email verification after 3 failures


def _send_verify_email(user, code):
    """
    Send the 6-digit verification code to the user's email.
    Falls back to flash message if SMTP is not configured (demo mode).
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        import os
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        if smtp_host and smtp_user:
            msg = MIMEText(
                f"Your VaultOS verification code is: {code}\n\n"
                f"This code expires in 10 minutes.\n"
                f"If you did not request this, please ignore this email."
            )
            msg['Subject'] = f'VaultOS Security Verification Code: {code}'
            msg['From'] = smtp_user
            msg['To'] = user.email
            with smtplib.SMTP(smtp_host, int(os.environ.get('SMTP_PORT', 587))) as s:
                s.starttls()
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
            return True
    except Exception:
        pass
    # SMTP not configured — code is shown in flash (demo mode)
    return False


@auth.route('/')
def index():
    return redirect(url_for('locker.dashboard') if current_user.is_authenticated else url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('locker.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not all([username, email, password]):
            flash('All fields are required.', 'danger'); return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger'); return render_template('register.html')
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger'); return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger'); return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger'); return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        log_event('REGISTER', resource=username, status='SUCCESS')
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('locker.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        user     = User.query.filter_by(username=username).first()

        if user and not user.is_active_acc:
            flash('Account is locked due to too many failed attempts. Contact admin.', 'danger')
            log_event('LOGIN', resource=username, status='BLOCKED')
            return render_template('login.html')

        if user and user.check_password(password):
            # ── Check if email verification is pending ────────────────────
            if user.failed_logins >= VERIFY_THRESHOLD and user.email_verify_code:
                session['pending_verify_user_id'] = user.id
                session['pending_verify_remember'] = remember
                flash('Please enter the verification code sent to your email.', 'warning')
                return redirect(url_for('auth.verify_email'))

            # ── Normal login ──────────────────────────────────────────────
            user.last_login    = datetime.now()
            user.login_count  += 1
            user.failed_logins = 0
            user.email_verify_code = None
            user.email_verify_expires = None
            db.session.commit()
            login_user(user, remember=remember)
            log_event('LOGIN', resource=username, status='SUCCESS')
            return redirect(request.args.get('next') or url_for('locker.dashboard'))
        else:
            if user:
                user.failed_logins += 1
                db.session.commit()

                if user.failed_logins >= MAX_FAILED:
                    user.is_active_acc = False
                    db.session.commit()
                    flash('Too many failed attempts. Account locked.', 'danger')
                    log_event('LOGIN', resource=username, status='BLOCKED',
                              details=f'{user.failed_logins} failed attempts')

                elif user.failed_logins >= VERIFY_THRESHOLD:
                    # ── Trigger email verification ────────────────────────
                    code = user.generate_verify_code()
                    db.session.commit()
                    email_sent = _send_verify_email(user, code)
                    session['pending_verify_user_id'] = user.id

                    masked_email = user.email[:2] + '***' + user.email[user.email.index('@'):]
                    if email_sent:
                        flash(f'⚠️ Suspicious activity detected. Verification code sent to {masked_email}.', 'warning')
                    else:
                        # Demo mode — show code directly
                        flash(f'⚠️ Suspicious activity detected. Your verification code is: {code} (sent to {masked_email})', 'warning')

                    log_event('LOGIN', resource=username, status='FAILURE',
                              details=f'{user.failed_logins} failed — email verification triggered')
                    return redirect(url_for('auth.verify_email'))
                else:
                    remaining = VERIFY_THRESHOLD - user.failed_logins
                    flash(f'Invalid credentials. {remaining} attempt(s) before verification is required.', 'danger')
                    log_event('LOGIN', resource=username, status='FAILURE')
            else:
                flash('Invalid credentials.', 'danger')
    return render_template('login.html')


@auth.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Email verification step after suspicious login activity."""
    pending_user_id = session.get('pending_verify_user_id')
    if not pending_user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(pending_user_id)
    if not user:
        session.pop('pending_verify_user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        if user.check_verify_code(code):
            # Code is correct — reset and log in
            session.pop('pending_verify_user_id', None)
            remember = session.pop('pending_verify_remember', False)
            user.last_login    = datetime.now()
            user.login_count  += 1
            user.failed_logins = 0
            user.email_verify_code = None
            user.email_verify_expires = None
            db.session.commit()
            login_user(user, remember=remember)
            log_event('LOGIN', resource=user.username, status='SUCCESS',
                      details='Email verification passed')
            flash('✅ Identity verified successfully!', 'success')
            return redirect(url_for('locker.dashboard'))
        else:
            flash('Invalid or expired verification code. Please try again.', 'danger')
            log_event('LOGIN', resource=user.username, status='FAILURE',
                      details='Email verification code rejected')

    masked_email = user.email[:2] + '***' + user.email[user.email.index('@'):]
    return render_template('email_verify.html', masked_email=masked_email)


@auth.route('/resend-code', methods=['POST'])
def resend_code():
    """Resend the email verification code."""
    pending_user_id = session.get('pending_verify_user_id')
    if not pending_user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(pending_user_id)
    if user:
        code = user.generate_verify_code()
        db.session.commit()
        email_sent = _send_verify_email(user, code)
        if email_sent:
            flash('A new verification code has been sent to your email.', 'info')
        else:
            flash(f'New verification code: {code}', 'info')
    return redirect(url_for('auth.verify_email'))


@auth.route('/logout')
@login_required
def logout():
    log_event('LOGOUT', status='SUCCESS')
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


# ── Forgot Password ──────────────────────────────────────────────────────────

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Step 1: Verify identity via username + email."""
    if current_user.is_authenticated:
        return redirect(url_for('locker.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()

        if not username or not email:
            flash('Both username and email are required.', 'danger')
            return render_template('forgot_password.html')

        user = User.query.filter_by(username=username, email=email).first()
        if user:
            if not user.is_active_acc:
                flash('This account is locked. Contact admin.', 'danger')
                return render_template('forgot_password.html')
            session['reset_user_id'] = user.id
            log_event('PASSWORD_RESET_REQUEST', resource=username, status='SUCCESS')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('No account found with that username and email combination.', 'danger')
            log_event('PASSWORD_RESET_REQUEST', resource=username, status='FAILURE',
                      details='Username/email mismatch')

    return render_template('forgot_password.html')


@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Step 2: Set new password after identity verification."""
    reset_user_id = session.get('reset_user_id')
    if not reset_user_id:
        flash('Please verify your identity first.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(reset_user_id)
    if not user:
        session.pop('reset_user_id', None)
        flash('User not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm      = request.form.get('confirm_password', '')

        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('reset_password.html', username=user.username)
        if new_password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', username=user.username)

        user.set_password(new_password)
        user.failed_logins = 0
        user.is_active_acc = True
        db.session.commit()
        session.pop('reset_user_id', None)
        log_event('PASSWORD_RESET', resource=user.username, status='SUCCESS')
        flash('✅ Password reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', username=user.username)
