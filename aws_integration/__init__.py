"""
AWS Integration Layer for VaultOS — Secure File Locker v2
==========================================================
FULLY OPTIONAL. The app works 100% without this.

Activates automatically when these environment variables are set:
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_REGION              (default: ap-south-1)
  AWS_S3_BUCKET           (required for S3 storage)
  AWS_SNS_TOPIC_ARN       (required for threat alerts)
  AWS_CLOUDWATCH_GROUP    (required for CloudWatch logging)

If these are NOT set, all AWS calls are silently skipped and
the app falls back to local disk + local audit log as normal.

Cost-safety tip: S3 and CloudWatch have free tiers.
SNS first 1,000 emails/month are free. Always set billing alerts.
"""

from aws_integration.config import aws_enabled, s3_enabled, sns_enabled, cloudwatch_enabled

__all__ = ['aws_enabled', 's3_enabled', 'sns_enabled', 'cloudwatch_enabled']
