from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.database.database import db
from models.user import User
import pyotp
import qrcode
import qrcode.image.svg
import os
import logging
import io
import base64

profile_bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)

@profile_bp.route('/', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    try:
        return jsonify({
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@profile_bp.route('/', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'username' in data:
            new_username = data['username'].strip()
            if len(new_username) < 3:
                return jsonify({'error': 'Username must be at least 3 characters long'}), 400
            
            # Check if username is already taken by another user
            existing_user = User.query.filter(
                User.username == new_username,
                User.id != current_user.id
            ).first()
            
            if existing_user:
                return jsonify({'error': 'Username already taken'}), 409
            
            current_user.username = new_username
        
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if '@' not in new_email:
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                User.email == new_email,
                User.id != current_user.id
            ).first()
            
            if existing_user:
                return jsonify({'error': 'Email already taken'}), 409
            
            current_user.email = new_email
        
        db.session.commit()
        
        logger.info(f"Profile updated for user: {current_user.email}")
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('current_password', 'new_password')):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

@profile_bp.route('/enable-2fa', methods=['POST'])
@login_required
def enable_2fa():
    """Enable 2FA and generate QR code"""
    try:
        if current_user.is_2fa_enabled:
            return jsonify({'error': '2FA is already enabled'}), 400
        
        # Generate new OTP secret
        otp_secret = current_user.generate_otp_secret()
        db.session.commit()
        
        # Generate QR code
        otp_uri = current_user.get_otp_uri()
        
        # Create QR code as SVG
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(otp_uri)
        qr.make(fit=True)
        
        # Create SVG image
        img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
        
        # Convert to base64 string
        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        logger.info(f"2FA setup initiated for user: {current_user.email}")
        
        return jsonify({
            'message': '2FA setup initiated. Scan the QR code with your authenticator app.',
            'qr_code': f"data:image/svg+xml;base64,{qr_code_data}",
            'otp_secret': otp_secret
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error enabling 2FA: {e}")
        return jsonify({'error': 'Failed to enable 2FA'}), 500

@profile_bp.route('/verify-2fa', methods=['POST'])
@login_required
def verify_2fa():
    """Verify 2FA setup and enable it"""
    try:
        data = request.get_json()
        
        if not data or 'otp_code' not in data:
            return jsonify({'error': 'OTP code is required'}), 400
        
        otp_code = data.get('otp_code')
        
        if not current_user.otp_secret:
            return jsonify({'error': '2FA setup not initiated'}), 400
        
        # Verify the OTP code
        if not current_user.verify_otp(otp_code):
            return jsonify({'error': 'Invalid OTP code'}), 401
        
        # Enable 2FA and generate recovery codes
        current_user.enable_2fa()
        recovery_codes = current_user.generate_recovery_codes()
        db.session.commit()
        
        logger.info(f"2FA enabled for user: {current_user.email}")
        
        return jsonify({
            'message': '2FA enabled successfully',
            'user': current_user.to_dict(),
            'recovery_codes': recovery_codes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error verifying 2FA: {e}")
        return jsonify({'error': 'Failed to verify 2FA'}), 500

@profile_bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    """Disable 2FA for the user"""
    try:
        data = request.get_json()
        
        if not current_user.is_2fa_enabled:
            return jsonify({'error': '2FA is not enabled'}), 400
        
        # Verify current password for security
        if not data or 'password' not in data:
            return jsonify({'error': 'Password is required to disable 2FA'}), 400
        
        password = data.get('password')
        if not current_user.check_password(password):
            return jsonify({'error': 'Incorrect password'}), 401
        
        # Disable 2FA
        current_user.disable_2fa()
        db.session.commit()
        
        logger.info(f"2FA disabled for user: {current_user.email}")
        
        return jsonify({
            'message': '2FA disabled successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error disabling 2FA: {e}")
        return jsonify({'error': 'Failed to disable 2FA'}), 500

@profile_bp.route('/regenerate-recovery-codes', methods=['POST'])
@login_required
def regenerate_recovery_codes():
    """Regenerate recovery codes for 2FA"""
    try:
        if not current_user.is_2fa_enabled:
            return jsonify({'error': '2FA is not enabled'}), 400
        
        # Verify current password for security
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({'error': 'Password is required to regenerate recovery codes'}), 400
        
        password = data.get('password')
        if not current_user.check_password(password):
            return jsonify({'error': 'Incorrect password'}), 401
        
        # Generate new recovery codes
        recovery_codes = current_user.generate_recovery_codes()
        db.session.commit()
        
        logger.info(f"Recovery codes regenerated for user: {current_user.email}")
        
        return jsonify({
            'message': 'Recovery codes regenerated successfully',
            'recovery_codes': recovery_codes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error regenerating recovery codes: {e}")
        return jsonify({'error': 'Failed to regenerate recovery codes'}), 500

@profile_bp.route('/2fa-status', methods=['GET'])
@login_required
def get_2fa_status():
    """Get 2FA status for the current user"""
    try:
        return jsonify({
            'is_2fa_enabled': current_user.is_2fa_enabled,
            'has_otp_secret': bool(current_user.otp_secret),
            'has_recovery_codes': current_user.has_recovery_codes(),
            'recovery_codes_count': len(current_user.get_recovery_codes())
        }), 200
    except Exception as e:
        logger.error(f"Error getting 2FA status: {e}")
        return jsonify({'error': 'Failed to get 2FA status'}), 500
