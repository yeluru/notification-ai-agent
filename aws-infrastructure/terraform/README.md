# Terraform Infrastructure for Notification Agent

This directory contains Terraform configuration to deploy the Notification Agent infrastructure on AWS.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Terraform** >= 1.0 installed
4. **Domain name** (optional, for custom domain)

## Quick Start

### 1. Configure Variables

Copy the example environment file and fill in your values:

```bash
cp config/env.example terraform.tfvars
```

Edit `terraform.tfvars` with your configuration:

```hcl
aws_region = "us-east-1"
app_name = "notification-agent"
environment = "prod"

llm_api_key = "sk-..."
ses_from_email = "notifications@example.com"
jwt_secret = "your-secret-key-here"
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Deploy Infrastructure

```bash
terraform apply
```

### 5. Deploy Frontend

After infrastructure is created, upload the frontend:

```bash
# Get S3 bucket name from outputs
terraform output s3_bucket_name

# Upload frontend files
cd ../../frontend
aws s3 sync . s3://$(terraform -chdir=../../aws-infrastructure/terraform output -raw s3_bucket_name) --exclude "*.md" --exclude ".git/*"
```

### 6. Update Frontend Configuration

Update `frontend/js/config.js` with the API Gateway URL from Terraform outputs:

```bash
terraform output api_gateway_url
```

## Infrastructure Components

### DynamoDB Tables
- `users` - User accounts
- `data_sources` - Email account configurations
- `notifications` - Notification records
- `sync_state` - Sync state tracking

### S3 + CloudFront
- Frontend static website hosting
- Optional CloudFront CDN for custom domain

### Lambda Functions
- `user-management` - Authentication and user management
- `data-source-config` - Data source configuration
- `process-notifications` - Main processing function
- `summarize` - LLM summarization
- `deliver` - Notification delivery
- `status-check` - Status and statistics

### API Gateway
- REST API for frontend
- CORS enabled
- JWT authentication

### EventBridge
- Scheduled rule to trigger processing every 15 minutes

### SQS Queues
- `summarization-queue` - Queue for summarization jobs
- `delivery-queue` - Queue for delivery jobs

### Secrets Manager
- Stores encrypted email credentials

## Cost Estimation

For 1000 active users:
- **DynamoDB**: ~$50-100/month (on-demand)
- **Lambda**: ~$20-50/month
- **API Gateway**: ~$10-30/month
- **Secrets Manager**: ~$400/month (or ~$40 with Parameter Store)
- **S3 + CloudFront**: ~$10-20/month
- **SQS**: ~$0.40/month
- **Total**: ~$500-600/month (or ~$150-200 with Parameter Store)

## Security Notes

1. **JWT Secret**: Generate a strong random secret:
   ```bash
   openssl rand -hex 32
   ```

2. **SES Verification**: Verify your sender email in SES console before deployment

3. **IAM Roles**: Lambda functions use least-privilege IAM roles

4. **Secrets**: Sensitive values stored in Secrets Manager or Parameter Store

## Troubleshooting

### Frontend not loading
- Check S3 bucket policy allows public read
- Verify CloudFront distribution is deployed (if using custom domain)
- Check browser console for CORS errors

### API Gateway errors
- Verify Lambda function names match
- Check CloudWatch logs for Lambda errors
- Verify API Gateway integration settings

### Lambda timeouts
- Increase Lambda timeout in `lambda.tf`
- Check CloudWatch logs for errors
- Verify DynamoDB table permissions

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy
```

**Warning**: This will delete all data in DynamoDB tables and S3 buckets!

## Next Steps

After deployment:
1. Verify SES sender email
2. Configure custom domain (optional)
3. Set up monitoring and alerts
4. Configure backup strategy
5. Review and optimize costs

