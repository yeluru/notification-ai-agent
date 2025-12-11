# Notification Agent Frontend

Modern, responsive web interface for the Notification Agent service. Built with vanilla JavaScript, HTML, and CSS for easy deployment to S3.

## Features

- **User Authentication** - Sign up, login, and session management
- **Dashboard** - Real-time statistics and activity monitoring
- **Data Source Management** - Add, configure, and manage email accounts
- **Settings** - Configure notification preferences and delivery methods
- **Responsive Design** - Works on desktop, tablet, and mobile devices

## Structure

```
frontend/
├── index.html          # Main application page
├── error.html          # Error page for S3
├── css/
│   └── styles.css      # All styles
├── js/
│   ├── config.js       # API configuration
│   ├── auth.js         # Authentication management
│   ├── api.js          # API client
│   ├── dashboard.js    # Dashboard functionality
│   ├── sources.js      # Data sources management
│   ├── settings.js     # Settings management
│   └── app.js          # Main application controller
└── images/             # Image assets (optional)
```

## Configuration

Before deploying, update the API configuration in `js/config.js`:

```javascript
const API_CONFIG = {
    apiEndpoint: 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod',
    cognito: {
        userPoolId: 'us-east-1_XXXXXXXXX',
        clientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
        region: 'us-east-1'
    }
};
```

Or set these as environment variables that get injected during build:

```html
<script>
    window.API_ENDPOINT = '${API_ENDPOINT}';
    window.COGNITO_USER_POOL_ID = '${COGNITO_USER_POOL_ID}';
    window.COGNITO_CLIENT_ID = '${COGNITO_CLIENT_ID}';
    window.COGNITO_REGION = '${COGNITO_REGION}';
</script>
```

## Deployment to S3

### 1. Build (if needed)

No build step required - files are ready to deploy as-is.

### 2. Create S3 Bucket

```bash
aws s3 mb s3://notification-agent-frontend
```

### 3. Configure S3 for Static Website Hosting

```bash
aws s3 website s3://notification-agent-frontend \
    --index-document index.html \
    --error-document error.html
```

### 4. Set Bucket Policy for Public Read

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::notification-agent-frontend/*"
        }
    ]
}
```

### 5. Upload Files

```bash
aws s3 sync . s3://notification-agent-frontend --exclude "*.md" --exclude ".git/*"
```

### 6. Enable CORS (if needed)

Create `cors.json`:

```json
{
    "CORSRules": [
        {
            "AllowedOrigins": ["*"],
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "HEAD"],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

```bash
aws s3api put-bucket-cors --bucket notification-agent-frontend --cors-configuration file://cors.json
```

## CloudFront Setup (Recommended)

For better performance and HTTPS:

1. Create CloudFront distribution
2. Set origin to S3 bucket
3. Configure custom error pages (404 → /error.html)
4. Set up custom domain (optional)
5. Configure SSL certificate

## API Integration

The frontend expects the following API endpoints:

- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication
- `GET /users/me` - Get current user
- `GET /data-sources` - List data sources
- `POST /data-sources` - Add data source
- `PUT /data-sources/{id}` - Update data source
- `DELETE /data-sources/{id}` - Delete data source
- `GET /notifications` - Get notifications
- `GET /stats` - Get statistics
- `GET /status` - Get system status
- `GET /settings` - Get user settings
- `PUT /settings` - Update user settings

All API requests require authentication via Bearer token in the `Authorization` header.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development

1. Serve files locally using a simple HTTP server:

```bash
python3 -m http.server 8000
# or
npx serve
```

2. Update `js/config.js` to point to your local API endpoint

3. Open `http://localhost:8000` in your browser

## Security Notes

- API keys and sensitive configuration should be injected at build/deploy time
- Never commit actual API endpoints or Cognito credentials to version control
- Use environment variables or build-time injection for configuration
- Enable HTTPS in production (via CloudFront or ALB)

