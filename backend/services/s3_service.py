"""
Local File Storage Service
Replaces AWS S3 for local development/demo
Files stored in /app/uploads folder inside Docker
Same interface as S3Service so no other code changes needed
"""
import os
import shutil
import mimetypes
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/app/uploads')


class S3Service:
    def __init__(self, access_key_id=None, secret_access_key=None,
                 region=None, bucket_name=None):
        self.bucket_name = bucket_name or 'local-storage'
        self.bucket_path = os.path.join(UPLOAD_DIR, self.bucket_name)
        os.makedirs(self.bucket_path, exist_ok=True)

    def _get_file_path(self, s3_key):
        safe_key = s3_key.replace('..', '').lstrip('/')
        return os.path.join(self.bucket_path, safe_key)

    def upload_file(self, file_obj, s3_key, content_type=None):
        try:
            file_path = self._get_file_path(s3_key)
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else self.bucket_path, exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(file_obj.read() if hasattr(file_obj, 'read') else file_obj)
            return True
        except Exception as e:
            raise Exception(f"Failed to save file: {e}")

    def download_file(self, s3_key):
        try:
            file_path = self._get_file_path(s3_key)
            if not os.path.exists(file_path):
                raise Exception("File not found")
            return open(file_path, 'rb')
        except Exception as e:
            raise Exception(f"Failed to read file: {e}")

    def delete_file(self, s3_key):
        try:
            file_path = self._get_file_path(s3_key)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file: {e}")

    def delete_folder(self, folder_path):
        try:
            full_path = self._get_file_path(folder_path)
            if os.path.exists(full_path):
                shutil.rmtree(full_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete folder: {e}")

    def create_folder(self, folder_path):
        try:
            full_path = self._get_file_path(folder_path)
            os.makedirs(full_path, exist_ok=True)
            return True
        except Exception as e:
            raise Exception(f"Failed to create folder: {e}")

    def generate_presigned_url(self, s3_key, expiration=3600):
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        token = hashlib.md5(f"{s3_key}{expiration}".encode()).hexdigest()
        return f"{base_url}/api/files/download-link/{token}?key={s3_key}&expires={expiration}"

    def get_file_info(self, s3_key):
        try:
            file_path = self._get_file_path(s3_key)
            if not os.path.exists(file_path):
                raise Exception("File not found")
            stat = os.stat(file_path)
            content_type, _ = mimetypes.guess_type(s3_key)
            return {
                'size': stat.st_size,
                'content_type': content_type or 'application/octet-stream',
                'last_modified': datetime.fromtimestamp(stat.st_mtime),
                'etag': hashlib.md5(s3_key.encode()).hexdigest()
            }
        except Exception as e:
            raise Exception(f"Failed to get file info: {e}")

    def test_connection(self):
        os.makedirs(self.bucket_path, exist_ok=True)
        return True
