"""
AWS S3 Storage Service — OPTIONAL
===================================
When S3 is enabled (AWS_S3_BUCKET set):
  - Encrypted .enc files are uploaded to S3 after local encryption
  - Downloads stream from S3 instead of local disk
  - Deletes remove the S3 object too

When S3 is NOT enabled:
  - All functions are no-ops that return False
  - The app uses local disk as before — zero behaviour change
"""
import os
from aws_integration.config import s3_enabled, get_client, AWS_S3_BUCKET

S3_PREFIX = 'encrypted-files/'   # folder inside your bucket


def upload_to_s3(local_path: str, stored_filename: str) -> bool:
    """
    Upload an encrypted file to S3.
    Returns True on success, False if S3 is disabled or upload fails.
    """
    if not s3_enabled:
        return False
    try:
        client = get_client('s3')
        s3_key = f'{S3_PREFIX}{stored_filename}'
        client.upload_file(
            local_path,
            AWS_S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',        # S3-side encryption on top of our AES-256
                'StorageClass': 'STANDARD_IA',           # cheaper for infrequent access
                'Metadata': {
                    'vault-encrypted': 'true',
                    'original-stored-name': stored_filename,
                }
            }
        )
        print(f'[S3] Uploaded: {s3_key}')
        return True
    except Exception as e:
        print(f'[S3] Upload failed (falling back to local): {e}')
        return False


def download_from_s3(stored_filename: str, local_dest_path: str) -> bool:
    """
    Download an encrypted file from S3 to a local temp path.
    Returns True on success, False if S3 is disabled or file not found.
    """
    if not s3_enabled:
        return False
    try:
        client = get_client('s3')
        s3_key = f'{S3_PREFIX}{stored_filename}'
        client.download_file(AWS_S3_BUCKET, s3_key, local_dest_path)
        print(f'[S3] Downloaded: {s3_key}')
        return True
    except Exception as e:
        print(f'[S3] Download failed (falling back to local): {e}')
        return False


def delete_from_s3(stored_filename: str) -> bool:
    """
    Delete an encrypted file from S3.
    Returns True on success, False if S3 is disabled or fails.
    """
    if not s3_enabled:
        return False
    try:
        client = get_client('s3')
        s3_key = f'{S3_PREFIX}{stored_filename}'
        client.delete_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
        print(f'[S3] Deleted: {s3_key}')
        return True
    except Exception as e:
        print(f'[S3] Delete failed: {e}')
        return False


def get_s3_file_url(stored_filename: str, expires_in: int = 3600) -> str | None:
    """
    Generate a pre-signed download URL for a file (valid for expires_in seconds).
    Returns None if S3 is disabled.
    """
    if not s3_enabled:
        return None
    try:
        client = get_client('s3')
        s3_key = f'{S3_PREFIX}{stored_filename}'
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_S3_BUCKET, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        print(f'[S3] Presigned URL failed: {e}')
        return None


def list_s3_files() -> list:
    """List all encrypted files in the S3 bucket prefix. For admin use."""
    if not s3_enabled:
        return []
    try:
        client = get_client('s3')
        response = client.list_objects_v2(Bucket=AWS_S3_BUCKET, Prefix=S3_PREFIX)
        return [
            {
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
            }
            for obj in response.get('Contents', [])
        ]
    except Exception as e:
        print(f'[S3] List failed: {e}')
        return []
