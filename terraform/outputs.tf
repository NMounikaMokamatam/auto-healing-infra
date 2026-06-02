output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "instance_public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.app.public_ip
}

output "instance_public_dns" {
  description = "EC2 public DNS"
  value       = aws_instance.app.public_dns
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alarms"
  value       = aws_sns_topic.alarms.arn
}

output "lambda_function_name" {
  description = "Auto-healing Lambda function name"
  value       = aws_lambda_function.auto_heal.function_name
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
