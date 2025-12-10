# Deployment Plan: AWS Multi-Tenant Notification Agent

## Quick Start Guide

### Prerequisites
- AWS Account
- AWS CLI configured
- Terraform or AWS CDK installed
- Domain name (optional, for custom domain)

### Step 1: Infrastructure Setup

#### Option A: Terraform (Recommended)
```bash
# Create infrastructure directory
mkdir -p aws-infrastructure/terraform
cd aws-infrastructure/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy
terraform apply
```

#### Option B: AWS CDK
```bash
# Install CDK
npm install -g aws-cdk

# Initialize project
cdk init app --language python

# Deploy
cdk deploy
```

### Step 2: Core Services Setup

#### 1. DynamoDB Tables
```bash
aws dynamodb create-table \
  --table-name users \
  --attribute-definitions AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

#### 2. Cognito User Pool
```bash
aws cognito-idp create-user-pool \
  --pool-name notification-agent-users \
  --auto-verified-attributes email
```

#### 3. Secrets Manager Setup
- Create KMS key for encryption
- Set up IAM policies for Lambda access

### Step 3: Lambda Functions

#### Function Structure
```
lambda-functions/
├── user-management/
│   ├── handler.py
│   └── requirements.txt
├── data-source-config/
│   ├── handler.py
│   └── requirements.txt
├── process-notifications/
│   ├── handler.py
│   └── requirements.txt
├── summarize/
│   ├── handler.py
│   └── requirements.txt
└── deliver/
    ├── handler.py
    └── requirements.txt
```

### Step 4: Frontend Deployment

#### Build Next.js App
```bash
cd frontend
npm install
npm run build
npm run export

# Upload to S3
aws s3 sync out/ s3://notification-agent-frontend/
```

#### CloudFront Distribution
```bash
aws cloudfront create-distribution \
  --origin-domain-name notification-agent-frontend.s3.amazonaws.com
```

### Step 5: Environment Variables

#### Lambda Environment Variables
- `DYNAMODB_TABLE_USERS`: users
- `DYNAMODB_TABLE_DATA_SOURCES`: data_sources
- `DYNAMODB_TABLE_NOTIFICATIONS`: notifications
- `SECRETS_MANAGER_REGION`: us-east-1
- `LLM_API_KEY`: (from Secrets Manager)
- `TWILIO_ACCOUNT_SID`: (from Secrets Manager)

### Step 6: EventBridge Schedule

```bash
aws events put-rule \
  --name process-notifications-schedule \
  --schedule-expression "rate(10 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule process-notifications-schedule \
  --targets "Id=1,Arn=arn:aws:lambda:REGION:ACCOUNT:function:process-notifications"
```

## Security Checklist

- [ ] Enable DynamoDB encryption at rest
- [ ] Use VPC for Lambda (if needed)
- [ ] Enable CloudTrail logging
- [ ] Set up WAF for API Gateway
- [ ] Configure CORS properly
- [ ] Enable MFA for AWS console
- [ ] Rotate access keys regularly
- [ ] Use IAM roles, not access keys
- [ ] Enable AWS GuardDuty (optional)

## Monitoring Setup

### CloudWatch Dashboards
1. **User Activity**: Sign-ups, active users
2. **Processing Metrics**: Lambda invocations, errors
3. **Queue Metrics**: SQS depth, processing time
4. **Cost Tracking**: Estimated costs per service

### Alarms
- Lambda error rate > 5%
- Queue depth > 1000
- API Gateway 5xx errors
- DynamoDB throttling

## Testing Strategy

### Unit Tests
- Lambda function logic
- Data validation
- Encryption/decryption

### Integration Tests
- API Gateway → Lambda → DynamoDB
- EventBridge → Lambda
- SQS → Lambda

### End-to-End Tests
- User signup → Configure source → Receive notification

## Rollout Plan

### Phase 1: Internal Testing (Week 1-2)
- Deploy to AWS
- Test with 5-10 internal users
- Fix critical bugs

### Phase 2: Beta (Week 3-4)
- Invite 50-100 beta users
- Collect feedback
- Monitor performance

### Phase 3: Public Launch (Week 5+)
- Open registration
- Marketing campaign
- Scale infrastructure as needed

## Cost Monitoring

### Set Up Billing Alerts
```bash
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget file://budget.json
```

### Budget Template
```json
{
  "BudgetName": "notification-agent-monthly",
  "BudgetLimit": {
    "Amount": "1000",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

## Maintenance

### Regular Tasks
- **Weekly**: Review CloudWatch logs for errors
- **Monthly**: Review costs and optimize
- **Quarterly**: Security audit, dependency updates
- **As needed**: Scale DynamoDB, add Lambda concurrency

### Backup Strategy
- DynamoDB: Point-in-time recovery (enable)
- Secrets: Automatic backup in Secrets Manager
- Code: Git repository (GitHub/GitLab)

## Disaster Recovery

### Backup Plan
1. DynamoDB point-in-time recovery
2. Secrets Manager automatic backups
3. Infrastructure as code (Terraform/CDK)
4. Lambda function code in Git

### Recovery Steps
1. Restore DynamoDB from backup
2. Redeploy Lambda functions
3. Verify API Gateway configuration
4. Test end-to-end flow

## Support & Documentation

### User Documentation
- Getting started guide
- API documentation
- Troubleshooting guide
- FAQ

### Developer Documentation
- Architecture overview
- Code structure
- Deployment guide
- Contributing guidelines

