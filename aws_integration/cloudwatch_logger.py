"""
AWS CloudWatch Logging Service — OPTIONAL
==========================================
When CloudWatch is enabled (AWS_CLOUDWATCH_GROUP set):
  - Every audit event (upload, download, login, delete, share)
    is also sent to CloudWatch Logs in structured JSON format
  - Enables centralized log analysis, dashboards, and alarms
    in the AWS Console at zero extra code cost

When CloudWatch is NOT enabled:
  - push_log_event() is a no-op, returns False silently
  - Local DB audit log still works as normal
"""
import json
import time
from datetime import datetime
from aws_integration.config import (
    cloudwatch_enabled, get_client,
    AWS_CLOUDWATCH_GROUP, AWS_CLOUDWATCH_STREAM
)

# CloudWatch requires a sequence token for ordered puts
# We store it in memory (resets on restart — acceptable for logging)
_sequence_token: str | None = None


def _ensure_log_group_and_stream():
    """Create the log group and stream if they don't exist yet."""
    client = get_client('logs')
    if not client:
        return None

    # Create log group (idempotent)
    try:
        client.create_log_group(logGroupName=AWS_CLOUDWATCH_GROUP)
        # Set 90-day retention to avoid unbounded costs
        client.put_retention_policy(
            logGroupName=AWS_CLOUDWATCH_GROUP,
            retentionInDays=90
        )
    except client.exceptions.ResourceAlreadyExistsException:
        pass
    except Exception:
        pass

    # Create log stream (idempotent)
    try:
        client.create_log_stream(
            logGroupName=AWS_CLOUDWATCH_GROUP,
            logStreamName=AWS_CLOUDWATCH_STREAM
        )
    except Exception:
        pass

    return client


def push_log_event(action: str, user_id: int = None, username: str = None,
                   resource: str = None, status: str = 'SUCCESS',
                   threat_score: float = 0.0, ip_address: str = None,
                   details: str = None) -> bool:
    """
    Push a structured audit event to CloudWatch Logs.
    Returns True on success, False if disabled or failed.
    """
    if not cloudwatch_enabled:
        return False

    global _sequence_token

    try:
        client = _ensure_log_group_and_stream()
        if not client:
            return False

        log_entry = {
            'timestamp':    datetime.utcnow().isoformat() + 'Z',
            'action':       action,
            'user_id':      user_id,
            'username':     username or 'unknown',
            'resource':     resource,
            'status':       status,
            'threat_score': round(threat_score, 4),
            'ip_address':   ip_address,
            'details':      details,
            'source':       'VaultOS',
        }

        event = {
            'timestamp': int(time.time() * 1000),   # milliseconds
            'message':   json.dumps(log_entry)
        }

        kwargs = {
            'logGroupName':  AWS_CLOUDWATCH_GROUP,
            'logStreamName': AWS_CLOUDWATCH_STREAM,
            'logEvents':     [event],
        }
        if _sequence_token:
            kwargs['sequenceToken'] = _sequence_token

        response = client.put_log_events(**kwargs)
        _sequence_token = response.get('nextSequenceToken')
        return True

    except Exception as e:
        # CloudWatch errors must NEVER break the app
        print(f'[CloudWatch] Log push failed (non-critical): {e}')
        _sequence_token = None   # reset token on error
        return False


def get_recent_logs(limit: int = 50) -> list:
    """
    Fetch the most recent log events from CloudWatch.
    Used in admin dashboard to show cloud logs.
    Returns empty list if CloudWatch is disabled.
    """
    if not cloudwatch_enabled:
        return []
    try:
        client = get_client('logs')
        response = client.get_log_events(
            logGroupName=AWS_CLOUDWATCH_GROUP,
            logStreamName=AWS_CLOUDWATCH_STREAM,
            limit=limit,
            startFromHead=False
        )
        events = []
        for e in response.get('events', []):
            try:
                data = json.loads(e['message'])
                data['_ts_ms'] = e['timestamp']
                events.append(data)
            except Exception:
                events.append({'message': e['message'], '_ts_ms': e['timestamp']})
        return list(reversed(events))
    except Exception as e:
        print(f'[CloudWatch] Fetch failed: {e}')
        return []
