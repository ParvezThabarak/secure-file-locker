from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.database.database import db
from models.user import User
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        username = data.get('username').strip()
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Validation
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during registration: {e}")
        return jsonify({'error': 'An error occurred during registration'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            logger.warning(f"Failed login attempt for email: {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if 2FA is enabled
        if user.is_2fa_enabled:
            otp_code = data.get('otp_code')
            recovery_code = data.get('recovery_code')
            
            if not otp_code and not recovery_code:
                return jsonify({
                    'error': '2FA code or recovery code required',
                    'requires_2fa': True
                }), 401
            
            # Try OTP code first
            if otp_code:
                if not user.verify_otp(otp_code):
                    logger.warning(f"Failed 2FA attempt for user: {email}")
                    return jsonify({'error': 'Invalid 2FA code'}), 401
            # Try recovery code if OTP failed or not provided
            elif recovery_code:
                if not user.verify_recovery_code(recovery_code):
                    logger.warning(f"Failed recovery code attempt for user: {email}")
                    return jsonify({'error': 'Invalid recovery code'}), 401
                else:
                    # Save the change to database
                    db.session.commit()
        
        # Login successful
        login_user(user, remember=data.get('remember', False))
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({'error': 'An error occurred during login'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    try:
        user_email = current_user.email
        logout_user()
        logger.info(f"User logged out: {user_email}")
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({'error': 'An error occurred during logout'}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    try:
        return jsonify({
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return jsonify({'error': 'An error occurred'}), 500
