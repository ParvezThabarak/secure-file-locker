from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.database.database import db
from models.file import File
from services.s3_service import S3Service
import logging
import io
import os
import json
from services.ml_service import AnomalyDetector
from models.access_log import AccessLog

files_bp = Blueprint('files', __name__)
logger = logging.getLogger(__name__)

def get_user_s3_service():
    """Get local file storage service (no AWS needed for local demo)"""
    return S3Service(bucket_name=f"user_{current_user.id}")

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload a file to S3 and save metadata to database"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        folder_path = request.form.get('folder_path', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Check file size (100MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 500 * 1024 * 1024:  # 500MB
            return jsonify({'error': 'File too large. Maximum size is 500MB'}), 413
        
        # Get S3 service
        s3_service = get_user_s3_service()
        
        # Create S3 key with folder path
        s3_key = f"{folder_path}{filename}" if folder_path else filename
        
        # Check if file already exists
        existing_file = File.query.filter_by(
            user_id=current_user.id,
            s3_key=s3_key
        ).first()
        
        if existing_file:
            return jsonify({'error': 'File with this name already exists in this folder'}), 409
        
        # Upload to S3
        content_type = file.content_type or 'application/octet-stream'
        s3_service.upload_file(file, s3_key, content_type)
        
        # Save metadata to database
        file_record = File(
            user_id=current_user.id,
            filename=filename,
            s3_key=s3_key,
            file_size=file_size,
            content_type=content_type,
            folder_path=folder_path,
            is_folder=False
        )
        
        db.session.add(file_record)
        db.session.commit()
        
        logger.info(f"File uploaded: {filename} by user {current_user.id}")

        # ML anomaly detection
        detector = AnomalyDetector(current_user.id)
        risk = detector.analyze('upload')
        log = AccessLog(user_id=current_user.id, action='upload',
            filename=filename, file_size=file_size,
            ip_address=request.remote_addr,
            risk_score=risk['risk_score'], risk_level=risk['risk_level'],
            alerts=json.dumps(risk['alerts']))
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'message': 'File uploaded successfully',
            'file': file_record.to_dict(),
            'security': {'risk_level': risk['risk_level'], 'risk_score': risk['risk_score']}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@files_bp.route('/create-folder', methods=['POST'])
@login_required
def create_folder():
    """Create a new folder"""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name', '').strip()
        parent_folder_path = data.get('parent_folder_path', '')
        
        if not folder_name:
            return jsonify({'error': 'Folder name is required'}), 400
        
        # Secure the folder name
        folder_name = secure_filename(folder_name)
        
        # Create full folder path
        full_folder_path = f"{parent_folder_path}{folder_name}/" if parent_folder_path else f"{folder_name}/"
        
        # Check if folder already exists
        existing_folder = File.query.filter_by(
            user_id=current_user.id,
            s3_key=full_folder_path,
            is_folder=True
        ).first()
        
        if existing_folder:
            return jsonify({'error': 'Folder with this name already exists'}), 409
        
        # Get S3 service
        s3_service = get_user_s3_service()
        
        # Create folder in S3
        s3_service.create_folder(full_folder_path)
        
        # Save folder metadata to database
        folder_record = File(
            user_id=current_user.id,
            filename=folder_name,
            s3_key=full_folder_path,
            file_size=0,
            content_type='application/x-directory',
            folder_path=parent_folder_path,
            is_folder=True
        )
        
        db.session.add(folder_record)
        db.session.commit()
        
        logger.info(f"Folder created: {folder_name} by user {current_user.id}")
        
        return jsonify({
            'message': 'Folder created successfully',
            'folder': folder_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating folder: {e}")
        return jsonify({'error': str(e)}), 500

@files_bp.route('/', methods=['GET'])
@login_required
def list_files():
    """List files and folders for the current user"""
    try:
        folder_path = request.args.get('folder_path', '')
        per_page = min(int(request.args.get('per_page', 50)), 100)
        page = int(request.args.get('page', 1))
        
        # Build query
        query = File.query.filter_by(user_id=current_user.id)
        
        if folder_path:
            # Show files that are inside this folder
            # folder_path should match the s3_key of the parent folder
            query = query.filter_by(folder_path=folder_path)
        else:
            # Show files in root folder (no parent folder)
            query = query.filter((File.folder_path == '') | (File.folder_path.is_(None)))
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        files = query.order_by(File.is_folder.desc(), File.filename.asc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'files': [file.to_dict() for file in files.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': files.pages,
                'has_next': files.has_next,
                'has_prev': files.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    """Download a file from S3"""
    try:
        # Get file record
        file_record = File.query.filter_by(
            id=file_id,
            user_id=current_user.id,
            is_folder=False
        ).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Get S3 service
        s3_service = get_user_s3_service()
        
        # Download file from S3
        file_obj = s3_service.download_file(file_record.s3_key)
        
        # Create response
        response = send_file(
            io.BytesIO(file_obj.read()),
            as_attachment=True,
            download_name=file_record.filename,
            mimetype=file_record.content_type
        )
        
        logger.info(f"File downloaded: {file_record.filename} by user {current_user.id}")

        # ML anomaly detection
        detector = AnomalyDetector(current_user.id)
        risk = detector.analyze('download')
        log = AccessLog(user_id=current_user.id, action='download',
            filename=file_record.filename, file_size=file_record.file_size,
            ip_address=request.remote_addr,
            risk_score=risk['risk_score'], risk_level=risk['risk_level'],
            alerts=json.dumps(risk['alerts']))
        db.session.add(log)
        db.session.commit()

        return response
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    """Delete a file or folder from S3 and database"""
    try:
        # Get file record
        file_record = File.query.filter_by(
            id=file_id,
            user_id=current_user.id
        ).first()
        
        if not file_record:
            return jsonify({'error': 'File or folder not found'}), 404
        
        # Get S3 service
        s3_service = get_user_s3_service()
        
        if file_record.is_folder:
            # Delete folder and all its contents
            s3_service.delete_folder(file_record.s3_key)
            
            # Delete all files in this folder from database
            File.query.filter_by(
                user_id=current_user.id,
                folder_path=file_record.s3_key
            ).delete()
        else:
            # Delete single file
            s3_service.delete_file(file_record.s3_key)
        
        # Delete the record from database
        db.session.delete(file_record)
        db.session.commit()
        
        logger.info(f"File/folder deleted: {file_record.filename} by user {current_user.id}")

        # ML anomaly detection
        detector = AnomalyDetector(current_user.id)
        risk = detector.analyze('delete')
        log = AccessLog(user_id=current_user.id, action='delete',
            filename=file_record.filename,
            ip_address=request.remote_addr,
            risk_score=risk['risk_score'], risk_level=risk['risk_level'],
            alerts=json.dumps(risk['alerts']))
        db.session.add(log)
        db.session.commit()

        return jsonify({'message': 'File or folder deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': str(e)}), 500

@files_bp.route('/stats', methods=['GET'])
@login_required
def get_file_stats():
    """Get file statistics for the current user"""
    try:
        # Get total files count
        total_files = File.query.filter_by(
            user_id=current_user.id,
            is_folder=False
        ).count()
        
        # Get total folders count
        total_folders = File.query.filter_by(
            user_id=current_user.id,
            is_folder=True
        ).count()
        
        # Get total size
        total_size = db.session.query(db.func.sum(File.file_size)).filter_by(
            user_id=current_user.id,
            is_folder=False
        ).scalar() or 0
        
        # Format total size
        def format_size(size):
            # Convert to float to handle Decimal types from database
            size = float(size)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        
        return jsonify({
            'total_files': total_files,
            'total_folders': total_folders,
            'total_size': total_size,
            'total_size_formatted': format_size(total_size)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting file stats: {e}")
        return jsonify({'error': str(e)}), 500

@files_bp.route('/<int:file_id>/share', methods=['POST'])
@login_required
def share_file(file_id):
    """Generate a presigned URL for file sharing"""
    try:
        # Get file record
        file_record = File.query.filter_by(
            id=file_id,
            user_id=current_user.id,
            is_folder=False
        ).first()
        
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        # Get S3 service
        s3_service = get_user_s3_service()
        
        # Expiry options: 1hr=3600, 24hr=86400, 7days=604800
        expiry_map = {'1hr': 3600, '24hr': 86400, '7days': 604800}
        req_data = request.get_json(silent=True) or {}
        expiry_key = req_data.get('expiry', '1hr')
        expiration = expiry_map.get(expiry_key, 3600)

        share_url = s3_service.generate_presigned_url(file_record.s3_key, expiration=expiration)

        logger.info(f"File shared: {file_record.filename} by user {current_user.id} expiry={expiry_key}")

        return jsonify({
            'share_url': share_url,
            'expires_in': expiration,
            'expiry_label': expiry_key,
            'filename': file_record.filename
        }), 200
        
    except Exception as e:
        logger.error(f"Error sharing file: {e}")
        return jsonify({'error': str(e)}), 500