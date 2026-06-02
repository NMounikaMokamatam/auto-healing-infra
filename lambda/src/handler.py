"""
Auto-Healing Lambda Function
Triggered by SNS → CloudWatch Alarm
Automatically restarts failed EC2 instances and sends Slack alerts
"""

import json
import logging
import os
from datetime import datetime

import boto3
import urllib.request
import urllib.error

# ── Logging ────────────────────────────────────────────────────
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ── AWS Clients ────────────────────────────────────────────────
ec2 = boto3.client("ec2", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# ── Config ─────────────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
INSTANCE_ID       = os.environ.get("INSTANCE_ID", "")
DRY_RUN           = os.environ.get("DRY_RUN", "false").lower() == "true"


def get_instance_state(instance_id: str) -> str:
    """Return current EC2 instance state."""
    try:
        resp = ec2.describe_instances(InstanceIds=[instance_id])
        state = resp["Reservations"][0]["Instances"][0]["State"]["Name"]
        logger.info(f"Instance {instance_id} state: {state}")
        return state
    except Exception as e:
        logger.error(f"Failed to describe instance {instance_id}: {e}")
        raise


def restart_instance(instance_id: str) -> dict:
    """Stop and start an EC2 instance."""
    logger.info(f"Restarting instance {instance_id} (dry_run={DRY_RUN})")

    if DRY_RUN:
        logger.info("DRY RUN — skipping actual restart")
        return {"action": "dry_run", "instance_id": instance_id}

    # Stop
    ec2.stop_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=[instance_id], WaiterConfig={"Delay": 10, "MaxAttempts": 30})
    logger.info(f"Instance {instance_id} stopped")

    # Start
    ec2.start_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id], WaiterConfig={"Delay": 10, "MaxAttempts": 30})
    logger.info(f"Instance {instance_id} started")

    return {"action": "restarted", "instance_id": instance_id}


def send_slack_alert(alarm_name: str, alarm_reason: str, action: str, instance_id: str) -> None:
    """Send a formatted Slack notification."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack alert")
        return

    emoji  = "✅" if action == "restarted" else "⚠️"
    color  = "#36a64f" if action == "restarted" else "#ff0000"
    ts     = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} Auto-Healing Triggered"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Alarm:*\n{alarm_name}"},
                            {"type": "mrkdwn", "text": f"*Instance:*\n`{instance_id}`"},
                            {"type": "mrkdwn", "text": f"*Action:*\n{action}"},
                            {"type": "mrkdwn", "text": f"*Time:*\n{ts}"},
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Reason:*\n{alarm_reason}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req  = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            logger.info(f"Slack response: {resp.status}")
    except urllib.error.URLError as e:
        logger.error(f"Failed to send Slack alert: {e}")


def parse_sns_message(event: dict) -> dict:
    """Extract alarm details from SNS event."""
    sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
    return {
        "alarm_name":   sns_message.get("AlarmName", "Unknown"),
        "alarm_reason": sns_message.get("NewStateReason", "Unknown"),
        "new_state":    sns_message.get("NewStateValue", "UNKNOWN"),
        "old_state":    sns_message.get("OldStateValue", "UNKNOWN"),
    }


def lambda_handler(event: dict, context) -> dict:
    """
    Main Lambda entry point.
    Triggered by SNS when CloudWatch alarm fires.
    """
    logger.info(f"Event received: {json.dumps(event)}")

    try:
        alarm = parse_sns_message(event)
        logger.info(f"Alarm: {alarm['alarm_name']} | State: {alarm['new_state']}")

        # Only act on ALARM state
        if alarm["new_state"] != "ALARM":
            logger.info(f"State is {alarm['new_state']} — no action needed")
            return {"statusCode": 200, "body": "No action needed"}

        if not INSTANCE_ID:
            raise ValueError("INSTANCE_ID environment variable not set")

        # Check current state before restarting
        current_state = get_instance_state(INSTANCE_ID)
        if current_state not in ("running", "stopped"):
            logger.warning(f"Instance in unexpected state: {current_state} — skipping")
            return {"statusCode": 200, "body": f"Skipped — state: {current_state}"}

        # Restart the instance
        result = restart_instance(INSTANCE_ID)

        # Alert Slack
        send_slack_alert(
            alarm_name=alarm["alarm_name"],
            alarm_reason=alarm["alarm_reason"],
            action=result["action"],
            instance_id=INSTANCE_ID
        )

        logger.info(f"Auto-healing complete: {result}")
        return {"statusCode": 200, "body": json.dumps(result)}

    except Exception as e:
        logger.error(f"Auto-healing failed: {e}", exc_info=True)
        send_slack_alert(
            alarm_name="Auto-Healing Lambda",
            alarm_reason=str(e),
            action="FAILED",
            instance_id=INSTANCE_ID or "unknown"
        )
        raise
