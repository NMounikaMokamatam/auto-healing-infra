variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev | staging | prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "auto-healing-infra"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into EC2"
  type        = string
  default     = "0.0.0.0/0"
}

variable "cpu_threshold" {
  description = "CPU % threshold to trigger alarm"
  type        = number
  default     = 80
}

variable "slack_webhook_url" {
  description = "Slack incoming webhook URL for alerts"
  type        = string
  sensitive   = true
  default     = ""
}

variable "dry_run" {
  description = "If true, Lambda logs actions but does not restart EC2"
  type        = bool
  default     = false
}
