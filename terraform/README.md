# Terraform — VaultOS AWS Infrastructure

This directory contains **Infrastructure-as-Code (IaC)** using Terraform to automatically provision the entire AWS stack for VaultOS cloud features.

## What Gets Created

| Resource | Purpose | Free Tier |
|----------|---------|-----------|
| **S3 Bucket** | Encrypted file storage with versioning | 5 GB / 20K requests |
| **SNS Topic** | Email alerts for HIGH/CRITICAL threats | 1,000 emails/month |
| **CloudWatch Log Group** | Cloud audit logs (90-day retention) | 5 GB ingestion/month |
| **IAM User** | Scoped app credentials (S3 + SNS + CW only) | Free |

## Prerequisites

1. [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) installed
2. [AWS CLI](https://aws.amazon.com/cli/) configured with an admin account
3. An AWS account (free tier is sufficient)

## Usage

```bash
# 1. Initialize Terraform
cd terraform
terraform init

# 2. Preview what will be created
terraform plan -var="notification_email=your@email.com"

# 3. Create all resources
terraform apply -var="notification_email=your@email.com"

# 4. View the outputs (your VaultOS env vars)
terraform output

# 5. Get the secret key (sensitive)
terraform output -raw iam_secret_access_key
```

## Feed Outputs into VaultOS

After `terraform apply`, set these environment variables:

```bash
export AWS_ACCESS_KEY_ID=$(terraform output -raw iam_access_key_id)
export AWS_SECRET_ACCESS_KEY=$(terraform output -raw iam_secret_access_key)
export AWS_REGION=$(terraform output -raw aws_region)
export AWS_S3_BUCKET=$(terraform output -raw s3_bucket_name)
export AWS_SNS_TOPIC_ARN=$(terraform output -raw sns_topic_arn)
export AWS_CLOUDWATCH_GROUP=$(terraform output -raw cloudwatch_log_group)
```

Then start VaultOS — cloud features will activate automatically.

## Destroy (Cleanup)

```bash
terraform destroy
```

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `ap-south-1` | AWS region |
| `project_name` | `vaultos` | Used in resource naming |
| `environment` | `dev` | dev / staging / prod |
| `notification_email` | `""` | Email for SNS alerts |

## Cost Safety

- All resources use AWS Free Tier by default
- S3 lifecycle transitions files to Infrequent Access after 90 days
- CloudWatch logs auto-expire after 90 days
- IAM user has **minimum-privilege** permissions
- Run `terraform destroy` when done to avoid any charges
