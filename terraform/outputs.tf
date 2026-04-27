# ── Outputs ─────────────────────────────────────────────────────────────────
# These values map directly to VaultOS environment variables.
# After `terraform apply`, set these in your .env or Jenkins credentials.

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "s3_bucket_name" {
  description = "S3 bucket name → set as AWS_S3_BUCKET"
  value       = aws_s3_bucket.vault.id
}

output "sns_topic_arn" {
  description = "SNS topic ARN → set as AWS_SNS_TOPIC_ARN"
  value       = aws_sns_topic.alerts.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group → set as AWS_CLOUDWATCH_GROUP"
  value       = aws_cloudwatch_log_group.audit.name
}

output "iam_access_key_id" {
  description = "IAM access key ID → set as AWS_ACCESS_KEY_ID"
  value       = aws_iam_access_key.vaultos.id
}

output "iam_secret_access_key" {
  description = "IAM secret key → set as AWS_SECRET_ACCESS_KEY"
  value       = aws_iam_access_key.vaultos.secret
  sensitive   = true
}
