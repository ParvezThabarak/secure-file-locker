"""
File Preview Blueprint
=======================
Decrypt files in memory and stream preview content to the browser.
Supports images (PNG, JPG, GIF), PDFs, and text/code files.
"""
import os, io, base64, mimetypes
from flask import (Blueprint, render_template, request, jsonify,
                   current_app, send_file, abort)
from flask_login import login_required, current_user
from app.models import LockedFile
from app.crypto_utils import decrypt_file
from app.audit import log_event

preview = Blueprint('preview', __name__)

# File types that can be previewed
PREVIEW_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif'}
PREVIEW_TEXT_EXT  = {'.txt', '.md', '.csv', '.py', '.js', '.html', '.css', '.log'}
PREVIEW_PDF_EXT   = {'.pdf'}
PREVIEWABLE_EXT   = PREVIEW_IMAGE_EXT | PREVIEW_TEXT_EXT | PREVIEW_PDF_EXT


def is_previewable(filename: str) -> bool:
    """Check if a file can be previewed in the browser."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in PREVIEWABLE_EXT


def get_preview_type(filename: str) -> str:
    """Return preview category: 'image', 'text', 'pdf', or 'none'."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in PREVIEW_IMAGE_EXT:
        return 'image'
    elif ext in PREVIEW_TEXT_EXT:
        return 'text'
    elif ext in PREVIEW_PDF_EXT:
        return 'pdf'
    return 'none'


@preview.route('/preview/<int:file_id>', methods=['GET', 'POST'])
@login_required
def preview_file(file_id):
    """Show preview page for a file."""
    lf = LockedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    ptype = get_preview_type(lf.original_filename)

    if ptype == 'none':
        abort(415, description='This file type cannot be previewed.')

    return render_template('preview.html', file=lf, preview_type=ptype)


@preview.route('/preview/<int:file_id>/content', methods=['POST'])
@login_required
def preview_content(file_id):
    """Decrypt file and return content for preview."""
    lf = LockedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    password = request.form.get('password', '').strip()

    if not password:
        return jsonify({'error': 'Password required'}), 400

    ptype = get_preview_type(lf.original_filename)
    if ptype == 'none':
        return jsonify({'error': 'File type not previewable'}), 415

    upload_folder = current_app.config['UPLOAD_FOLDER']
    enc_path = os.path.join(upload_folder, lf.stored_filename)
    dec_path = os.path.join(upload_folder, f"preview_{lf.stored_filename}")

    try:
        # Try local disk first; fall back to S3
        if not os.path.exists(enc_path):
            from aws_integration.s3_storage import download_from_s3
            download_from_s3(lf.stored_filename, enc_path)

        decrypt_file(enc_path, dec_path, password)
        log_event('PREVIEW', resource=lf.original_filename, status='SUCCESS')

        if ptype == 'image':
            # Return base64 data URL
            mime = mimetypes.guess_type(lf.original_filename)[0] or 'image/png'
            with open(dec_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
            return jsonify({
                'type': 'image',
                'data': f'data:{mime};base64,{data}',
                'filename': lf.original_filename
            })

        elif ptype == 'text':
            with open(dec_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(500_000)  # max 500KB of text
            return jsonify({
                'type': 'text',
                'data': content,
                'filename': lf.original_filename,
                'extension': os.path.splitext(lf.original_filename)[1].lower()
            })

        elif ptype == 'pdf':
            with open(dec_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
            return jsonify({
                'type': 'pdf',
                'data': f'data:application/pdf;base64,{data}',
                'filename': lf.original_filename
            })

    except Exception as e:
        log_event('PREVIEW', resource=lf.original_filename, status='FAILURE',
                  details=str(e))
        return jsonify({'error': 'Decryption failed. Wrong password?'}), 403

    finally:
        if os.path.exists(dec_path):
            os.remove(dec_path)
