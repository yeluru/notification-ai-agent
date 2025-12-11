# Setup Guide - Notification Agent

## Quick Start

### 1. Start Backend API

```bash
cd backend-api
npm install
npm run dev
```

Backend will run on `http://localhost:3000`

### 2. Start Frontend

```bash
cd frontend-react
npm install
npm run dev
```

Frontend will run on `http://localhost:3000` (Vite uses port 5173 by default, but check the terminal output)

### 3. Configure Environment Variables

#### Backend (`backend-api/.env`):
```env
PORT=3000
JWT_SECRET=dev-secret-change-in-production
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

#### Frontend (`frontend-react/.env`):
```env
VITE_API_URL=http://localhost:3000/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

## Google OAuth Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable Google+ API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized JavaScript origins: `http://localhost:5173` (or your frontend port)
7. Authorized redirect URIs: `http://localhost:5173`
8. Copy the **Client ID** to both `.env` files

## Testing Signup

1. Open `http://localhost:5173` (or the port shown in terminal)
2. Click "Sign up"
3. Fill in:
   - Email: `hemsra@gmail.com`
   - Password: (at least 8 characters)
   - Phone: `7037171010` (optional)
4. Click "Create Account"

Or use Google Sign-In button (if configured).

## Troubleshooting

### Signup fails
- Check backend is running on port 3000
- Check browser console for errors
- Verify API URL in frontend `.env`

### Google Sign-In not working
- Verify `GOOGLE_CLIENT_ID` is set in both `.env` files
- Check authorized origins in Google Console
- Make sure frontend URL matches authorized origin

### Port conflicts
- Backend uses port 3000 (change in `backend-api/.env`)
- Frontend uses port 5173 by default (Vite)
- Update `VITE_API_URL` if backend port changes

