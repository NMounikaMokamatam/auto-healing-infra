# Auto-Healing Infrastructure on AWS

Production-grade self-healing AWS infrastructure using EC2, CloudWatch Alarms, Lambda in Python 3.12 for auto-restart, and Slack alerting — all provisioned with Terraform.

## Architecture

EC2 instances emit metrics to CloudWatch. When CPU exceeds 80 percent or a status check fails, CloudWatch triggers an SNS topic. SNS invokes a Python Lambda function that automatically stops and restarts the affected EC2 instance, then sends a formatted Slack alert to the team with the instance ID, alarm name, and timestamp.

## Stack

- EC2: Application server with CloudWatch agent for metrics
- CloudWatch: Alarms for CPU, memory, and status checks plus a dashboard
- SNS: Fan-out from alarms to Lambda and Slack
- Lambda Python 3.12: Auto-restarts failed EC2 and sends Slack alerts
- Terraform: Full infrastructure including VPC, IAM, and CloudWatch
- GitHub Actions: Terraform plan on PRs, apply on merge to main

## Quick Start

Copy terraform.tfvars.example to terraform.tfvars and fill in your values. Run terraform init and terraform apply. To test auto-healing, run scripts/test-alarm.sh which manually sets the alarm to ALARM state and triggers the Lambda.

## GitHub Secrets Required

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- AWS_ACCOUNT_ID
- SLACK_WEBHOOK_URL
