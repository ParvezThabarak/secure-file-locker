"""
AWS SNS Threat Alert Service — OPTIONAL
=========================================
When SNS is enabled (AWS_SNS_TOPIC_ARN set):
  - Sends an email/SMS alert to the SNS topic whenever
    a HIGH or CRITICAL threat file is uploaded
  - Admin must subscribe their email to the SNS topic
    in the AWS Console (one-time setup)

When SNS is NOT enabled:
  - send_threat_alert() is a no-op, returns False silently
"""
from aws_integration.config import sns_enabled, get_client, AWS_SNS_TOPIC_ARN
from datetime import datetime


def send_threat_alert(filename: str, threat_level: str, threat_score: float,
                      username: str, category: str, anomaly_reason: str,
                      user_ip: str = 'unknown') -> bool:
    """
    Publish a threat alert to the SNS topic.
    Only fires for HIGH or CRITICAL threat levels.
    Returns True if sent, False if disabled or failed.
    """
    if not sns_enabled:
        return False

    if threat_level not in ('HIGH', 'CRITICAL'):
        return False    # Only alert on real threats, not LOW/MEDIUM

    try:
        client = get_client('sns')

        subject = f'[VaultOS] {threat_level} Threat Detected — {filename}'

        message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 VaultOS — THREAT ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A {threat_level} risk file was uploaded to VaultOS.

  File Name    : {filename}
  Threat Level : {threat_level}
  Threat Score : {threat_score:.3f} / 1.000
  ML Category  : {category.upper()}
  Uploaded By  : {username}
  User IP      : {user_ip}
  Anomaly Note : {anomaly_reason}
  Timestamp    : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action: Log in to VaultOS Admin → Threats to review.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        response = client.publish(
            TopicArn=AWS_SNS_TOPIC_ARN,
            Subject=subject,
            Message=message,
        )
        print(f'[SNS] Alert sent. MessageId: {response["MessageId"]}')
        return True

    except Exception as e:
        print(f'[SNS] Alert failed (non-critical): {e}')
        return False


def send_admin_summary(total_files: int, high_threats: int,
                       anomalies: int, period: str = 'daily') -> bool:
    """
    Send a periodic summary digest to the admin via SNS.
    Can be triggered by a scheduled Jenkins job or cron.
    """
    if not sns_enabled:
        return False
    try:
        client = get_client('sns')
        subject = f'[VaultOS] {period.title()} Security Summary'
        message = f"""
VaultOS — {period.title()} Security Summary
{datetime.utcnow().strftime('%Y-%m-%d UTC')}

  Total Files    : {total_files}
  High Threats   : {high_threats}
  Anomalies      : {anomalies}

Review the admin dashboard for full details.
"""
        client.publish(TopicArn=AWS_SNS_TOPIC_ARN, Subject=subject, Message=message)
        return True
    except Exception as e:
        print(f'[SNS] Summary failed: {e}')
        return False
