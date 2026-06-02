#!/usr/bin/env bash
# test-alarm.sh — Manually trigger CloudWatch alarm to test auto-healing
set -euo pipefail

REGION="${1:-us-east-1}"
PROJECT="${2:-auto-healing-infra}"
ALARM_NAME="${PROJECT}-status-check"

echo "==> Triggering alarm: $ALARM_NAME"
aws cloudwatch set-alarm-state \
  --alarm-name "$ALARM_NAME" \
  --state-value ALARM \
  --state-reason "Manual test trigger" \
  --region "$REGION"

echo "✅ Alarm triggered! Check Slack and Lambda logs:"
echo "   aws logs tail /aws/lambda/${PROJECT}-auto-heal --follow --region $REGION"
