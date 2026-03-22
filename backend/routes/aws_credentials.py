from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.database.database import db
from models.aws_credentials import AWSCredentials
import boto3
import logging

aws_credentials_bp = Blueprint('aws_credentials', __name__)
logger = logging.getLogger(__name__)

@aws_credentials_bp.route('/status', methods=['GET'])
@login_required
def get_credentials_status():
    """Get AWS credentials status for current user"""
    try:
        credentials = AWSCredentials.query.filter_by(user_id=current_user.id).first()
        
        if not credentials:
            return jsonify({
                'has_credentials': False,
                'message': 'No AWS credentials configured'
            }), 200
        
        if not credentials.is_active:
            return jsonify({
                'has_credentials': False,
                'message': 'AWS credentials are inactive'
            }), 200
        
        return jsonify({
            'has_credentials': True,
            'credentials': credentials.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting credentials status: {e}")
        return jsonify({'error': 'An error occurred while checking credentials status'}), 500

@aws_credentials_bp.route('/setup', methods=['POST'])
@login_required
def setup_credentials():
    """Setup AWS credentials for current user"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('access_key_id', 'secret_access_key', 'region', 'bucket_name')):
            return jsonify({'error': 'Missing required fields: access_key_id, secret_access_key, region, bucket_name'}), 400
        
        access_key_id = data.get('access_key_id').strip()
        secret_access_key = data.get('secret_access_key').strip()
        region = data.get('region').strip()
        bucket_name = data.get('bucket_name').strip()
        
        # Validate inputs
        if not all([access_key_id, secret_access_key, region, bucket_name]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Test AWS credentials by trying to access S3
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region
            )
            
            # Test credentials by listing buckets
            s3_client.list_buckets()
            
            # Test if we can access the specific bucket
            s3_client.head_bucket(Bucket=bucket_name)
            
        except Exception as e:
            logger.warning(f"Invalid AWS credentials for user {current_user.id}: {e}")
            return jsonify({'error': f'Invalid AWS credentials or bucket access denied: {str(e)}'}), 400
        
        # Check if user already has credentials
        existing_credentials = AWSCredentials.query.filter_by(user_id=current_user.id).first()
        
        if existing_credentials:
            # Update existing credentials
            existing_credentials.set_credentials(access_key_id, secret_access_key, region, bucket_name)
            db.session.commit()
            
            logger.info(f"Updated AWS credentials for user {current_user.id}")
            
            return jsonify({
                'message': 'AWS credentials updated successfully',
                'credentials': existing_credentials.to_dict()
            }), 200
        else:
            # Create new credentials
            credentials = AWSCredentials(user_id=current_user.id)
            credentials.set_credentials(access_key_id, secret_access_key, region, bucket_name)
            
            db.session.add(credentials)
            db.session.commit()
            
            logger.info(f"Created AWS credentials for user {current_user.id}")
            
            return jsonify({
                'message': 'AWS credentials configured successfully',
                'credentials': credentials.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting up AWS credentials: {e}")
        return jsonify({'error': 'An error occurred while setting up credentials'}), 500

@aws_credentials_bp.route('/test', methods=['POST'])
@login_required
def test_credentials():
    """Test AWS credentials without saving them"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('access_key_id', 'secret_access_key', 'region', 'bucket_name')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        access_key_id = data.get('access_key_id').strip()
        secret_access_key = data.get('secret_access_key').strip()
        region = data.get('region').strip()
        bucket_name = data.get('bucket_name').strip()
        
        # Test AWS credentials
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=region
            )
            
            # Test credentials by listing buckets
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            
            # Test if we can access the specific bucket
            s3_client.head_bucket(Bucket=bucket_name)
            
            return jsonify({
                'message': 'AWS credentials are valid',
                'available_buckets': buckets,
                'bucket_accessible': True
            }), 200
            
        except Exception as e:
            logger.warning(f"Invalid AWS credentials test: {e}")
            return jsonify({'error': f'Invalid AWS credentials or bucket access denied: {str(e)}'}), 400
            
    except Exception as e:
        logger.error(f"Error testing AWS credentials: {e}")
        return jsonify({'error': 'An error occurred while testing credentials'}), 500

@aws_credentials_bp.route('/remove', methods=['DELETE'])
@login_required
def remove_credentials():
    """Remove AWS credentials for current user"""
    try:
        credentials = AWSCredentials.query.filter_by(user_id=current_user.id).first()
        
        if not credentials:
            return jsonify({'error': 'No AWS credentials found'}), 404
        
        db.session.delete(credentials)
        db.session.commit()
        
        logger.info(f"Removed AWS credentials for user {current_user.id}")
        
        return jsonify({'message': 'AWS credentials removed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing AWS credentials: {e}")
        return jsonify({'error': 'An error occurred while removing credentials'}), 500
