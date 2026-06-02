#!/usr/bin/env bash
# bootstrap.sh — Deploy auto-healing infra from scratch
set -euo pipefail

REGION="${1:-us-east-1}"

echo "==> Initializing Terraform"
cd terraform
terraform init

echo "==> Validating config"
terraform validate

echo "==> Planning"
terraform plan -out=tfplan

echo "==> Applying"
terraform apply tfplan

echo ""
echo "✅ Auto-healing infra deployed!"
echo ""
terraform output
