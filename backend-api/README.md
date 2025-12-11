# Notification Agent - Backend API

Local development API server that matches the Lambda function structure.

## Features

- ✅ User authentication (signup, login)
- ✅ Google OAuth integration
- ✅ JWT token management
- ✅ Data sources management
- ✅ Notifications API
- ✅ Settings API

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env` file:

```env
PORT=3000
JWT_SECRET=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

### 3. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Set authorized JavaScript origins: `http://localhost:3000`
6. Set authorized redirect URIs: `http://localhost:3000`
7. Copy the Client ID to `.env`

### 4. Start Server

```bash
npm run dev
```

Server will run on `http://localhost:3000`

## API Endpoints

### Authentication

- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/google` - Google OAuth signin/signup
- `POST /api/auth/refresh` - Refresh token

### User

- `GET /api/users/me` - Get current user
- `PUT /api/users/me` - Update user

### Data Sources

- `GET /api/data-sources` - List sources
- `POST /api/data-sources` - Add source
- `PUT /api/data-sources/:id` - Update source
- `DELETE /api/data-sources/:id` - Delete source
- `POST /api/data-sources/:id/test` - Test connection

### Notifications

- `GET /api/notifications` - Get notifications
- `GET /api/stats` - Get statistics
- `GET /api/status` - Get system status

### Settings

- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

## Frontend Configuration

Update `frontend-react/.env`:

```env
VITE_API_URL=http://localhost:3000/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

## Notes

- Uses in-memory storage (data resets on restart)
- In production, replace with DynamoDB
- JWT tokens expire in 24 hours
- Google OAuth is optional (works without it)

