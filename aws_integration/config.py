"""
AWS configuration and availability detection.
All values come from environment variables — nothing is hardcoded.
"""
import os
import boto3
from botocore.exceptions import NoCredentialsError, EndpointResolutionError

# ── Read environment ──────────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID', '').strip()
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '').strip()
AWS_REGION            = os.environ.get('AWS_REGION', 'ap-south-1').strip()
AWS_S3_BUCKET         = os.environ.get('AWS_S3_BUCKET', '').strip()
AWS_SNS_TOPIC_ARN     = os.environ.get('AWS_SNS_TOPIC_ARN', '').strip()
AWS_CLOUDWATCH_GROUP  = os.environ.get('AWS_CLOUDWATCH_GROUP', 'VaultOS').strip()
AWS_CLOUDWATCH_STREAM = os.environ.get('AWS_CLOUDWATCH_STREAM', 'audit-log').strip()

# ── Availability flags ────────────────────────────────────────────────────────
aws_enabled        = bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)
s3_enabled         = aws_enabled and bool(AWS_S3_BUCKET)
sns_enabled        = aws_enabled and bool(AWS_SNS_TOPIC_ARN)
cloudwatch_enabled = aws_enabled and bool(AWS_CLOUDWATCH_GROUP)


def get_client(service: str):
    """Return a boto3 client for the given service, or None if AWS is not configured."""
    if not aws_enabled:
        return None
    try:
        return boto3.client(
            service,
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    except Exception as e:
        print(f'[AWS] Failed to create {service} client: {e}')
        return None


def check_aws_connectivity() -> dict:
    """
    Test connectivity to each enabled AWS service.
    Used in the admin dashboard to show AWS status.
    Returns a dict of { service: 'OK' | 'ERROR: ...' | 'DISABLED' }
    """
    results = {}

    # S3
    if s3_enabled:
        try:
            client = get_client('s3')
            client.head_bucket(Bucket=AWS_S3_BUCKET)
            results['s3'] = f'OK — bucket: {AWS_S3_BUCKET}'
        except Exception as e:
            results['s3'] = f'ERROR: {str(e)[:80]}'
    else:
        results['s3'] = 'DISABLED (set AWS_S3_BUCKET to enable)'

    # SNS
    if sns_enabled:
        try:
            client = get_client('sns')
            client.get_topic_attributes(TopicArn=AWS_SNS_TOPIC_ARN)
            results['sns'] = 'OK — topic reachable'
        except Exception as e:
            results['sns'] = f'ERROR: {str(e)[:80]}'
    else:
        results['sns'] = 'DISABLED (set AWS_SNS_TOPIC_ARN to enable)'

    # CloudWatch
    if cloudwatch_enabled:
        try:
            client = get_client('logs')
            client.describe_log_groups(logGroupNamePrefix=AWS_CLOUDWATCH_GROUP, limit=1)
            results['cloudwatch'] = f'OK — group: {AWS_CLOUDWATCH_GROUP}'
        except Exception as e:
            results['cloudwatch'] = f'ERROR: {str(e)[:80]}'
    else:
        results['cloudwatch'] = 'DISABLED (set AWS_CLOUDWATCH_GROUP to enable)'

    return results
