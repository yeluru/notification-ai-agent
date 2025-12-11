# Local Development Guide

This is a **vanilla JavaScript** application (not React). It's a single-page application (SPA) that can be run locally for UI preview.

## Quick Start

### Option 1: Use the provided script (easiest)

```bash
cd frontend
./start-local.sh
```

This will start a local server on port 8000 and open your browser.

### Option 2: Manual setup

#### Using Python (recommended)

```bash
cd frontend
python3 -m http.server 8000
```

Then open: `http://localhost:8000/index.local.html`

#### Using Node.js

```bash
cd frontend
npx serve
# or
npx http-server
```

#### Using PHP

```bash
cd frontend
php -S localhost:8000
```

## Important Notes

### ⚠️ API Calls Will Fail

The frontend is designed to connect to an AWS API Gateway backend. When running locally:

- **Login/Signup**: Mocked - you can use any email/password
- **API calls**: Will fail with CORS/network errors (this is expected)
- **UI Preview**: You can see and interact with the UI, but data won't persist

### Using `index.local.html`

The `index.local.html` file includes:
- Mock authentication (auto-login with any credentials)
- Local development banner
- Pre-filled demo credentials

### Using `index.html`

The regular `index.html` expects:
- API Gateway endpoint configured in `js/config.js`
- Real backend running
- CORS properly configured

## What You Can See

Even without the backend, you can preview:

1. **Login/Signup Pages** - Full UI with forms
2. **Dashboard** - Layout and design (with mock data)
3. **Data Sources Page** - UI for managing email accounts
4. **Settings Page** - Configuration UI
5. **Navigation** - All page transitions work
6. **Responsive Design** - Test on different screen sizes

## Connecting to Backend

To connect to a real backend:

1. Update `js/config.js` with your API Gateway URL:
   ```javascript
   apiEndpoint: 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod'
   ```

2. Use `index.html` instead of `index.local.html`

3. Ensure CORS is configured on your API Gateway

## Development Tips

### Hot Reload

For better development experience, consider using a tool with hot reload:

```bash
# Using live-server (npm package)
npm install -g live-server
cd frontend
live-server --port=8000
```

### Browser DevTools

- Open DevTools (F12) to see:
  - Console errors (expected for API calls)
  - Network requests (will fail without backend)
  - UI inspection and debugging

### Testing Different Screens

The UI is responsive. Test on:
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

Use browser DevTools device emulation.

## Troubleshooting

### Port already in use

```bash
# Use a different port
python3 -m http.server 8080
```

### CORS errors

This is expected when running locally. The frontend needs to connect to an API Gateway with CORS enabled.

### Styles not loading

Make sure you're running from the `frontend/` directory so relative paths work correctly.

### JavaScript errors

Check browser console. Some errors are expected when API calls fail.

## Next Steps

1. **Deploy Backend**: Set up AWS infrastructure to get real API endpoints
2. **Update Config**: Point `config.js` to your API Gateway
3. **Test End-to-End**: Full functionality requires backend

## Architecture

This is a **static site** that:
- Uses vanilla JavaScript (no build step)
- Can be deployed to S3
- Communicates with backend via REST API
- Uses JWT for authentication

No React, no build tools, just HTML/CSS/JS! 🎉

