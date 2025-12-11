# Notification Agent - React Frontend

Modern React application for the Notification Agent service. Built with React, Vite, and React Router.

## Features

- ✅ **Authentication** - Sign up, login, and session management
- ✅ **Dashboard** - Real-time statistics and activity monitoring
- ✅ **Data Sources** - Add, test, and manage email accounts
- ✅ **Settings** - Configure notification preferences
- ✅ **Responsive Design** - Works on all devices

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will open at `http://localhost:3000`

### Build for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:3000/api
```

For production, set to your API Gateway URL:

```env
VITE_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod
```

## Project Structure

```
frontend-react/
├── src/
│   ├── components/      # Reusable components
│   │   └── Layout.jsx   # Main layout with navigation
│   ├── pages/           # Page components
│   │   ├── LoginPage.jsx
│   │   ├── SignupPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── DataSourcesPage.jsx
│   │   └── SettingsPage.jsx
│   ├── context/         # React Context
│   │   └── AuthContext.jsx
│   ├── services/        # API services
│   │   └── api.js
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Entry point
├── public/              # Static assets
└── package.json
```

## Key Features

### Authentication Flow

1. User signs up or logs in
2. JWT token stored in localStorage
3. Token automatically added to API requests
4. Auto-refresh on 401 errors

### Data Sources Management

1. **Add Source** - Modal form to add email account
2. **Test Connection** - Verify credentials before saving
3. **Toggle Status** - Activate/pause data sources
4. **Delete** - Remove data sources

### Background Process Setup

Once a connection is successfully tested and saved:
- Data source is marked as `active`
- Background process automatically starts (via EventBridge)
- Processing runs every 15 minutes (configurable)

## Development

### Adding New Features

1. Create component in `src/components/`
2. Add route in `src/App.jsx`
3. Create API service in `src/services/api.js`
4. Add page in `src/pages/`

### API Integration

All API calls go through `src/services/api.js`:

```javascript
import { dataSourcesAPI } from '../services/api'

// List sources
const sources = await dataSourcesAPI.list()

// Create source
await dataSourcesAPI.create({ email, password, ... })

// Test connection
await dataSourcesAPI.test(sourceId)
```

## Deployment

### Build

```bash
npm run build
```

Output will be in `dist/` directory.

### Deploy to S3

```bash
# Build first
npm run build

# Upload to S3
aws s3 sync dist/ s3://your-bucket-name --delete
```

### Deploy to CloudFront

After uploading to S3, update your CloudFront distribution to point to the new build.

## Troubleshooting

### API calls failing

- Check `.env` file has correct `VITE_API_URL`
- Verify CORS is enabled on API Gateway
- Check browser console for errors

### Authentication not working

- Verify JWT token is being stored in localStorage
- Check API endpoint returns correct token format
- Ensure token refresh logic is working

## Next Steps

- [ ] Add real-time updates (WebSocket)
- [ ] Add more data source types (LinkedIn, Twitter)
- [ ] Add notification history page
- [ ] Add analytics dashboard
- [ ] Add dark mode

