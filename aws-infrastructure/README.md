# AWS Infrastructure for Notification Agent

Complete AWS infrastructure setup for the multi-tenant Notification Agent service.

## Structure

```
aws-infrastructure/
├── terraform/              # Terraform infrastructure as code
│   ├── main.tf             # Main configuration
│   ├── variables.tf        # Variable definitions
│   ├── dynamodb.tf        # DynamoDB tables
│   ├── s3.tf              # S3 bucket and CloudFront
│   ├── lambda.tf          # Lambda functions
│   ├── api-gateway.tf     # API Gateway
│   ├── eventbridge.tf     # EventBridge schedules
│   ├── sqs.tf             # SQS queues
│   └── outputs.tf         # Output values
├── config/                 # Configuration files
│   ├── env.example        # Environment variables template
│   └── api-gateway-routes.yaml  # API route documentation
└── scripts/                # Utility scripts
    └── build-lambda-packages.sh  # Build Lambda deployment packages
```

## Quick Start

### 1. Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Terraform >= 1.0 installed
- Python 3.11+ for Lambda functions

### 2. Configure

```bash
cd terraform
cp ../config/env.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Build Lambda Packages

```bash
../scripts/build-lambda-packages.sh
```

### 4. Deploy

```bash
terraform init
terraform plan
terraform apply
```

### 5. Deploy Frontend

```bash
# Get S3 bucket name
terraform output s3_bucket_name

# Upload frontend
cd ../../frontend
aws s3 sync . s3://$(terraform -chdir=../../aws-infrastructure/terraform output -raw s3_bucket_name) \
  --exclude "*.md" --exclude ".git/*"
```

## Architecture Overview

### Components

1. **Frontend (S3 + CloudFront)**
   - Static website hosting
   - Optional CloudFront CDN
   - Custom domain support

2. **API Gateway**
   - REST API for frontend
   - Lambda integration
   - CORS enabled

3. **Lambda Functions**
   - `user-management` - Authentication & user management
   - `data-source-config` - Email account configuration
   - `process-notifications` - Main processing (EventBridge trigger)
   - `summarize` - LLM summarization (SQS trigger)
   - `deliver` - Notification delivery (SQS trigger)
   - `status-check` - Status & statistics

4. **DynamoDB Tables**
   - `users` - User accounts
   - `data_sources` - Email configurations
   - `notifications` - Notification records
   - `sync_state` - Sync state tracking

5. **SQS Queues**
   - `summarization-queue` - Summarization jobs
   - `delivery-queue` - Delivery jobs

6. **EventBridge**
   - Scheduled rule (every 15 minutes)
   - Triggers `process-notifications`

7. **Secrets Manager**
   - Encrypted email credentials
   - Per-user secret storage

## Deployment Steps

### Step 1: Infrastructure Setup

```bash
cd terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### Step 2: Build and Deploy Lambda Functions

```bash
# Build packages
../scripts/build-lambda-packages.sh

# Update Lambda functions (if code changed)
# Note: Terraform will deploy on apply, but you can also update manually:
aws lambda update-function-code \
  --function-name notification-agent-user-management-prod \
  --zip-file fileb://../lambda-functions/user-management/deployment.zip
```

### Step 3: Deploy Frontend

```bash
cd ../../frontend

# Get bucket name from Terraform output
BUCKET=$(terraform -chdir=../../aws-infrastructure/terraform output -raw s3_bucket_name)

# Upload files
aws s3 sync . s3://$BUCKET \
  --exclude "*.md" \
  --exclude ".git/*" \
  --exclude "node_modules/*"

# Update frontend config with API Gateway URL
API_URL=$(terraform -chdir=../../aws-infrastructure/terraform output -raw api_gateway_url)
# Manually update frontend/js/config.js with API_URL
```

### Step 4: Verify SES Email

Before sending emails, verify your sender email in SES:

```bash
aws ses verify-email-identity --email-address notifications@example.com
```

### Step 5: Test

1. Access frontend: `terraform output s3_bucket_website_url`
2. Create account
3. Add email data source
4. Wait for processing (15 minutes or trigger manually)

## Configuration

### Environment Variables

Key variables in `terraform.tfvars`:

- `llm_api_key` - LLM provider API key
- `ses_from_email` - Verified SES sender email
- `jwt_secret` - JWT signing secret (generate with `openssl rand -hex 32`)
- `twilio_*` - Twilio credentials (optional, for SMS)

### Lambda Environment Variables

Set automatically by Terraform:
- DynamoDB table names
- SQS queue URLs
- AWS region
- LLM configuration
- SES/Twilio configuration

## Monitoring

### CloudWatch Logs

Each Lambda function has CloudWatch logs:
- `/aws/lambda/notification-agent-{function-name}-{environment}`

### CloudWatch Metrics

Monitor:
- Lambda invocations and errors
- DynamoDB read/write capacity
- SQS queue depth
- API Gateway request count

### Alarms

Set up alarms for:
- Lambda error rate > 5%
- SQS queue depth > 1000
- API Gateway 5xx errors

## Cost Optimization

1. **Use Parameter Store** instead of Secrets Manager for non-rotating secrets
2. **DynamoDB on-demand** billing (pay per request)
3. **S3 Intelligent-Tiering** for logs
4. **Lambda reserved concurrency** to prevent over-scaling
5. **API Gateway v2** (HTTP API) for lower costs

## Security

1. **IAM Roles**: Least privilege for Lambda functions
2. **Secrets Manager**: Encrypted credentials
3. **VPC**: Optional VPC for Lambda (if needed)
4. **WAF**: Optional Web Application Firewall
5. **HTTPS**: CloudFront SSL/TLS

## Troubleshooting

### Lambda Timeout

Increase timeout in `lambda.tf`:
```hcl
timeout = 300  # 5 minutes
```

### API Gateway CORS Errors

Check CORS configuration in `api-gateway.tf` and frontend `config.js`.

### DynamoDB Throttling

Switch to provisioned capacity or increase on-demand limits.

### Frontend Not Loading

- Check S3 bucket policy
- Verify CloudFront distribution (if using)
- Check browser console for errors

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy -var-file=terraform.tfvars
```

**Warning**: This deletes all data!

## Next Steps

1. Set up monitoring dashboards
2. Configure backup strategy
3. Set up CI/CD pipeline
4. Add custom domain
5. Enable CloudTrail logging
6. Set up cost alerts

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review Terraform plan output
3. Verify IAM permissions
4. Check AWS service quotas

