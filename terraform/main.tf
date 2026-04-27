# ─────────────────────────────────────────────────────────────────────────────
# VaultOS — Terraform Infrastructure-as-Code
# Provisions the complete AWS stack for optional cloud features.
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  prefix = "${var.project_name}-${var.environment}"
}

# ── S3 Bucket (encrypted file storage) ────────────────────────────────────

resource "aws_s3_bucket" "vault" {
  bucket        = "${local.prefix}-vault-storage"
  force_destroy = var.environment == "dev" ? true : false

  tags = {
    Name        = "${local.prefix}-vault-storage"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "vault" {
  bucket = aws_s3_bucket.vault.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "vault" {
  bucket = aws_s3_bucket.vault.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "vault" {
  bucket = aws_s3_bucket.vault.id
  rule {
    id     = "transition-to-ia"
    status = "Enabled"
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "vault" {
  bucket                  = aws_s3_bucket.vault.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── SNS Topic (threat alerts via email) ───────────────────────────────────

resource "aws_sns_topic" "alerts" {
  name = "${local.prefix}-threat-alerts"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# ── CloudWatch Log Group (audit logs) ─────────────────────────────────────

resource "aws_cloudwatch_log_group" "audit" {
  name              = "/vaultos/${var.environment}/audit"
  retention_in_days = 90

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_stream" "audit_stream" {
  name           = "audit-log"
  log_group_name = aws_cloudwatch_log_group.audit.name
}

# ── IAM User (scoped permissions for VaultOS app) ─────────────────────────

resource "aws_iam_user" "vaultos" {
  name = "${local.prefix}-app-user"

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_iam_access_key" "vaultos" {
  user = aws_iam_user.vaultos.name
}

resource "aws_iam_user_policy" "vaultos" {
  name = "${local.prefix}-app-policy"
  user = aws_iam_user.vaultos.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:HeadBucket"
        ]
        Resource = [
          aws_s3_bucket.vault.arn,
          "${aws_s3_bucket.vault.arn}/*"
        ]
      },
      {
        Sid    = "SNSPublish"
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:GetTopicAttributes"
        ]
        Resource = aws_sns_topic.alerts.arn
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents"
        ]
        Resource = [
          aws_cloudwatch_log_group.audit.arn,
          "${aws_cloudwatch_log_group.audit.arn}:*"
        ]
      }
    ]
  })
}
