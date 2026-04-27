"""
REST API + JWT Authentication Blueprint
=========================================
Provides a programmatic JSON API for all VaultOS operations.
External applications authenticate via JWT Bearer tokens.
"""
import os, io, uuid, mimetypes, datetime
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import jwt

from app import db
from app.models import User, LockedFile
from app.crypto_utils import encrypt_file, decrypt_file
from app.audit import log_event
from ml_engine import compute_threat_score

api = Blueprint('api', __name__, url_prefix='/api/v1')

ALLOWED_EXT = {
    'txt','pdf','png','jpg','jpeg','gif','docx','xlsx','pptx',
    'zip','mp4','mp3','csv','py','js','html','md','tar','gz'
}

def _get_secret():
    return current_app.config.get('SECRET_KEY', 'dev-secret')

def generate_token(user_id, username, is_admin=False):
    payload = {
        'user_id': user_id, 'username': username, 'is_admin': is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, _get_secret(), algorithm='HS256')

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Missing Authorization header'}), 401
        try:
            payload = jwt.decode(auth.split(' ',1)[1], _get_secret(), algorithms=['HS256'])
            request._jwt_payload = payload
            request._jwt_user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_jwt_required(f):
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if not request._jwt_payload.get('is_admin'):
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated

def _get_user():
    return User.query.get(request._jwt_user_id)

@api.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username','').strip()
    password = data.get('password','')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    if not user.is_active_acc:
        return jsonify({'error': 'Account locked'}), 403
    token = generate_token(user.id, user.username, user.is_admin)
    return jsonify({'token': token, 'expires_in': 3600,
                    'user': {'id': user.id, 'username': user.username, 'is_admin': user.is_admin}})

@api.route('/files', methods=['GET'])
@jwt_required
def list_files():
    user = _get_user()
    if not user: return jsonify({'error': 'User not found'}), 404
    files = LockedFile.query.filter_by(user_id=user.id, parent_id=None).order_by(LockedFile.upload_time.desc()).all()
    return jsonify({'files': [{'id':f.id,'filename':f.original_filename,'size':f.file_size,
        'type':f.file_type,'upload_time':f.upload_time.isoformat(),'download_count':f.download_count,
        'version':f.version,'tags':f.tags,'ml_category':f.ml_file_category,
        'ml_threat_score':f.ml_threat_score,'ml_is_anomaly':f.ml_is_anomaly} for f in files],
        'total': len(files), 'storage_used': user.storage_used, 'storage_quota': user.storage_quota})

@api.route('/files/upload', methods=['POST'])
@jwt_required
def upload_file():
    user = _get_user()
    if not user: return jsonify({'error':'User not found'}), 404
    file = request.files.get('file')
    password = request.form.get('password','').strip()
    if not file or not file.filename: return jsonify({'error':'No file'}), 400
    if len(password) < 6: return jsonify({'error':'Password >= 6 chars'}), 400
    ext = file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXT: return jsonify({'error':f'.{ext} not allowed'}), 400
    if user.storage_used >= user.storage_quota: return jsonify({'error':'Quota exceeded'}), 413
    orig = secure_filename(file.filename); uid = str(uuid.uuid4()); stored = f"{uid}.enc"
    uf = current_app.config['UPLOAD_FOLDER']; tmp = os.path.join(uf,f"{uid}_tmp"); enc = os.path.join(uf,stored)
    try:
        file.save(tmp); sz = os.path.getsize(tmp)
        ft = mimetypes.guess_type(orig)[0] or 'application/octet-stream'
        fe = os.path.splitext(orig)[1].lower()
        ml = compute_threat_score(orig, sz, user_failed_logins=user.failed_logins)
        encrypt_file(tmp, enc, password)
        lf = LockedFile(original_filename=orig,stored_filename=stored,file_size=sz,file_type=ft,
            file_extension=fe,encrypted=True,user_id=user.id,
            description=request.form.get('description','').strip(),
            tags=request.form.get('tags','').strip(),
            ml_file_category=ml['category'],ml_threat_score=ml['score'],
            ml_is_anomaly=ml['is_anomaly'],ml_confidence=ml['confidence'])
        db.session.add(lf); user.storage_used += sz; db.session.commit()
        log_event('API_UPLOAD', resource=orig, status='SUCCESS', threat_score=ml['score'])
        return jsonify({'message':'Uploaded','file':{'id':lf.id,'filename':orig,'ml_threat_score':ml['score'],'ml_threat_level':ml['level']}}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(tmp): os.remove(tmp)

@api.route('/files/<int:file_id>', methods=['GET'])
@jwt_required
def get_file(file_id):
    user = _get_user()
    lf = LockedFile.query.filter_by(id=file_id, user_id=user.id).first()
    if not lf: return jsonify({'error':'Not found'}), 404
    thr,_ = lf.threat_label()
    return jsonify({'id':lf.id,'filename':lf.original_filename,'size':lf.file_size,'type':lf.file_type,
        'upload_time':lf.upload_time.isoformat(),'download_count':lf.download_count,'version':lf.version,
        'description':lf.description,'tags':lf.tags,'ml_category':lf.ml_file_category,
        'ml_threat_score':lf.ml_threat_score,'ml_threat_level':thr,'ml_is_anomaly':lf.ml_is_anomaly})

@api.route('/files/<int:file_id>/download', methods=['POST'])
@jwt_required
def download_file(file_id):
    user = _get_user()
    lf = LockedFile.query.filter_by(id=file_id, user_id=user.id).first()
    if not lf: return jsonify({'error':'Not found'}), 404
    data = request.get_json(silent=True) or {}
    pw = data.get('password','').strip()
    if not pw: return jsonify({'error':'Password required'}), 400
    uf = current_app.config['UPLOAD_FOLDER']
    enc = os.path.join(uf, lf.stored_filename); dec = os.path.join(uf, f"api_dec_{lf.stored_filename}")
    try:
        if not os.path.exists(enc):
            from aws_integration.s3_storage import download_from_s3
            download_from_s3(lf.stored_filename, enc)
        decrypt_file(enc, dec, pw); lf.download_count += 1; db.session.commit()
        log_event('API_DOWNLOAD', resource=lf.original_filename, status='SUCCESS')
        return send_file(dec, as_attachment=True, download_name=lf.original_filename, mimetype=lf.file_type)
    except Exception:
        if os.path.exists(dec): os.remove(dec)
        return jsonify({'error':'Decryption failed'}), 403

@api.route('/files/<int:file_id>', methods=['DELETE'])
@jwt_required
def delete_file(file_id):
    user = _get_user()
    lf = LockedFile.query.filter_by(id=file_id, user_id=user.id).first()
    if not lf: return jsonify({'error':'Not found'}), 404
    uf = current_app.config['UPLOAD_FOLDER']; enc = os.path.join(uf, lf.stored_filename)
    try:
        if os.path.exists(enc): os.remove(enc)
        from aws_integration.s3_storage import delete_from_s3
        delete_from_s3(lf.stored_filename)
        user.storage_used = max(0, user.storage_used - lf.file_size)
        name = lf.original_filename; db.session.delete(lf); db.session.commit()
        log_event('API_DELETE', resource=name, status='SUCCESS')
        return jsonify({'message': f'{name} deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/ml/scan', methods=['POST'])
@jwt_required
def ml_scan():
    data = request.get_json(silent=True) or {}
    return jsonify(compute_threat_score(data.get('filename',''), int(data.get('size',0))))

@api.route('/admin/stats', methods=['GET'])
@admin_jwt_required
def admin_stats():
    from sqlalchemy import func
    from ml_engine import get_ml_stats
    return jsonify({
        'total_users': User.query.count(),
        'total_files': LockedFile.query.count(),
        'total_storage_bytes': db.session.query(func.sum(LockedFile.file_size)).scalar() or 0,
        'high_threats': LockedFile.query.filter(LockedFile.ml_threat_score > 0.6).count(),
        'anomalies': LockedFile.query.filter_by(ml_is_anomaly=True).count(),
        'ml_stats': get_ml_stats(),
    })
