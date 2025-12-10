# AWS Architecture Design for Multi-Tenant Notification Agent

## Overview
A scalable, secure, privacy-preserving notification aggregation service that monitors multiple data sources (Email, LinkedIn, Twitter, etc.) and sends personalized summaries via SMS/Email.

## Core Principles
1. **User Data Ownership**: Each user's data is isolated and encrypted
2. **Privacy First**: Credentials encrypted at rest, minimal data retention
3. **Scalability**: Serverless architecture that scales automatically
4. **Cost-Effective**: Pay-per-use model
5. **User-Friendly**: Modern web UI for configuration

## Architecture Components

### 1. Frontend (User Interface)
**Technology**: Next.js (React) with TypeScript
**Hosting**: 
- Static assets: S3 + CloudFront CDN
- API routes: Lambda@Edge or API Gateway
**Features**:
- User authentication (AWS Cognito)
- Dashboard for monitoring status
- Configuration UI for data sources
- Notification preferences
- Usage analytics

### 2. Backend API
**Technology**: AWS Lambda (Python/Node.js) + API Gateway
**Functions**:
- `UserManagement`: Sign up, profile, preferences
- `DataSourceConfig`: Add/remove/update data sources (email, LinkedIn, Twitter)
- `NotificationConfig`: SMS/Email delivery settings
- `StatusCheck`: Real-time status of monitoring jobs
- `WebhookReceiver`: Receive OAuth callbacks (LinkedIn, Twitter)

### 3. Data Storage

#### User Data (DynamoDB)
**Table: `users`**
- `user_id` (Partition Key)
- `email`, `phone`, `preferences`
- `created_at`, `updated_at`
- `subscription_tier` (Free, Pro, Enterprise)

**Table: `data_sources`**
- `user_id` (Partition Key)
- `source_id` (Sort Key)
- `source_type` (email, linkedin, twitter)
- `credentials_encrypted` (encrypted with user-specific key)
- `config` (IMAP settings, OAuth tokens, etc.)
- `status` (active, paused, error)
- `last_sync_at`

**Table: `notifications`**
- `user_id` (Partition Key)
- `notification_id` (Sort Key)
- `source_type`, `source_id`
- `content`, `summary`
- `delivered_at`, `delivery_method`
- `created_at`

**Table: `sync_state`**
- `user_id` (Partition Key)
- `source_id` (Sort Key)
- `last_sync_timestamp`
- `last_processed_item_id`
- `error_count`, `last_error`

#### Secrets Management
**AWS Secrets Manager** (or Parameter Store for cost savings)
- Encrypted credentials per user
- Automatic rotation support
- Access via IAM roles

### 4. Processing Layer

#### Scheduled Jobs (EventBridge)
**Rule**: Run every 10-15 minutes
**Target**: Lambda function `ProcessNotifications`

**Lambda: `ProcessNotifications`**
- Reads active data sources from DynamoDB
- For each user/source:
  - Fetches new items (emails, posts, tweets)
  - Filters by last_sync_timestamp
  - Stores in `notifications` table
  - Updates `sync_state`
- Triggers summarization if new items found

#### Summarization Queue (SQS)
**Queue**: `summarization-queue`
- Triggered when new notifications arrive
- Lambda: `SummarizeNotifications`
  - Groups notifications by user
  - Calls LLM API (OpenAI/Anthropic)
  - Stores summary
  - Triggers delivery

#### Delivery Queue (SQS)
**Queue**: `delivery-queue`
- Lambda: `DeliverNotifications`
  - Reads summaries from queue
  - Sends via Twilio (SMS) or SES (Email)
  - Updates delivery status

### 5. Data Source Integrations

#### Email (IMAP)
- Stored credentials in Secrets Manager
- Lambda connects via IMAP
- Processes unread emails since last sync

#### LinkedIn
- OAuth 2.0 flow
- Store refresh tokens in Secrets Manager
- Use LinkedIn API (or web scraping with user consent)
- Rate limiting per user

#### Twitter/X
- OAuth 1.0a or 2.0
- Twitter API v2
- Store tokens in Secrets Manager
- Rate limiting per user

### 6. Security & Privacy

#### Encryption
- **At Rest**: DynamoDB encryption (AWS KMS)
- **In Transit**: TLS/HTTPS everywhere
- **Credentials**: Encrypted in Secrets Manager
- **User-specific keys**: Optional per-user KMS keys

#### Access Control
- **IAM Roles**: Least privilege for Lambda functions
- **VPC**: Optional VPC for Lambda (if needed)
- **API Authentication**: AWS Cognito JWT tokens
- **Rate Limiting**: API Gateway throttling

#### Data Isolation
- **Partition Key**: `user_id` ensures data isolation
- **Row-level security**: Lambda enforces user context
- **Audit Logs**: CloudTrail for all API calls

### 7. Monitoring & Logging

#### CloudWatch
- **Logs**: Lambda execution logs
- **Metrics**: 
  - Processing latency
  - Error rates
  - Queue depth
  - User activity
- **Alarms**: Error thresholds, queue backup

#### X-Ray (Optional)
- Distributed tracing
- Performance monitoring

### 8. Cost Optimization

#### Free Tier Considerations
- DynamoDB: 25GB free, on-demand pricing
- Lambda: 1M requests/month free
- SQS: 1M requests/month free
- Secrets Manager: $0.40/secret/month (consider Parameter Store for non-rotating secrets)

#### Cost-Saving Strategies
- Use Parameter Store for non-rotating secrets
- DynamoDB on-demand pricing (pay per request)
- S3 Intelligent-Tiering for logs
- Lambda reserved concurrency (prevent over-scaling)

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFront CDN                            │
│              (Static Assets + API Gateway)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌─────────▼──────────┐
│   S3 Bucket    │          │   API Gateway      │
│  (Next.js App) │          │  (REST API)        │
└────────────────┘          └─────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
            ┌───────▼──────┐   ┌───────▼──────┐   ┌───────▼──────┐
            │   Lambda     │   │   Lambda     │   │   Lambda     │
            │ UserMgmt API │   │ DataSource   │   │ Notification │
            └───────┬──────┘   └───────┬──────┘   └───────┬──────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                         │                          │
    ┌───────▼────────┐      ┌─────────▼──────────┐    ┌─────────▼──────────┐
    │   DynamoDB     │      │ Secrets Manager    │    │   EventBridge     │
    │  (User Data)   │      │  (Credentials)     │    │  (Scheduler)      │
    └───────┬────────┘      └────────────────────┘    └─────────┬──────────┘
            │                                                  │
            │                                    ┌─────────────▼──────────┐
            │                                    │   Lambda: Process      │
            │                                    │   Notifications        │
            │                                    └─────────────┬──────────┘
            │                                                  │
            │                          ┌───────────────────────┼───────────────────────┐
            │                          │                       │                       │
    ┌───────▼────────┐      ┌──────────▼──────────┐  ┌─────────▼──────────┐  ┌─────────▼──────────┐
    │   SQS Queue   │      │   Lambda:           │  │   Lambda:         │  │   Lambda:         │
    │ Summarization  │─────▶│ Summarize          │  │ Deliver (SMS)     │  │ Deliver (Email)   │
    └────────────────┘      └────────────────────┘  └──────────────────┘  └──────────────────┘
                                                              │
                                                              │
                                                    ┌─────────▼──────────┐
                                                    │   Twilio / SES     │
                                                    │  (Delivery)        │
                                                    └────────────────────┘
```

## Implementation Phases

### Phase 1: MVP (Email Only)
1. User authentication (Cognito)
2. Email source configuration
3. Basic processing (IMAP)
4. Email delivery (SES)
5. Simple web UI

### Phase 2: Multi-Source
1. LinkedIn integration (OAuth)
2. Twitter integration (OAuth)
3. Enhanced UI for multiple sources
4. Source-specific filtering

### Phase 3: Advanced Features
1. Custom LLM prompts per user
2. Notification scheduling preferences
3. Analytics dashboard
4. Mobile app (optional)

### Phase 4: Enterprise
1. Team/organization support
2. SSO integration
3. Advanced security (VPC, WAF)
4. Compliance (SOC2, GDPR)

## Security Best Practices

1. **Credential Storage**
   - Never log credentials
   - Use Secrets Manager with encryption
   - Rotate credentials regularly

2. **API Security**
   - JWT tokens with short expiration
   - Rate limiting per user
   - Input validation and sanitization

3. **Data Privacy**
   - Minimal data collection
   - User data deletion on request
   - Encryption at rest and in transit
   - Audit logs for compliance

4. **Access Control**
   - IAM roles with least privilege
   - User context validation in Lambda
   - No cross-user data access

## Estimated Costs (1000 Active Users)

- **DynamoDB**: ~$50-100/month (on-demand)
- **Lambda**: ~$20-50/month (1M+ invocations)
- **API Gateway**: ~$10-30/month
- **Secrets Manager**: ~$400/month (1000 secrets)
- **SQS**: ~$0.40/month (minimal)
- **S3 + CloudFront**: ~$10-20/month
- **EventBridge**: Free (first 1M events)
- **Total**: ~$500-600/month

**Cost Optimization**: Use Parameter Store for non-rotating secrets → Save ~$360/month

## Next Steps

1. Create AWS account and set up IAM roles
2. Set up infrastructure as code (Terraform/CDK)
3. Build MVP with email support
4. Implement authentication and UI
5. Add LinkedIn/Twitter integrations
6. Deploy and test with beta users

