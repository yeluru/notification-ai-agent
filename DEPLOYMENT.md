# Deployment Guide - Render.com

This guide explains how to deploy the Notification Agent (Email & SMS) to Render.com as a cron job.

## Prerequisites

1. A GitHub account
2. A Render.com account (free tier works)
3. All your email app passwords ready
4. Twilio account (for SMS) or email setup (for email notifications)
5. OpenAI API key (or compatible LLM API)

## Step 1: Push to GitHub

1. Initialize git repository (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Email notification agent"
   ```

2. Create a new repository on GitHub

3. Push to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/notification-agent.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy on Render.com

### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create the cron job
5. Configure environment variables (see Step 3)

### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Cron Job"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `notification-agent`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m linkedin_sms_agent.main --method email`
   - **Schedule**: `*/15 * * * *` (every 15 minutes)
5. Configure environment variables (see Step 3)

## Step 3: Configure Environment Variables

In Render dashboard, go to your cron job → Environment → Add Environment Variable:

### Required Variables

**Email Accounts:**
```
EMAIL_ACCOUNTS=your-email@gmail.com,another-email@outlook.com
EMAIL_PASSWORD_your-email@gmail.com=your-app-password
EMAIL_PASSWORD_another-email@outlook.com=your-app-password
```

**Notification:**
```
SEND_SUMMARY_FROM_EMAIL=your-sender@gmail.com
SEND_SUMMARY_TO_EMAIL=your-recipient@example.com
NOTIFICATION_METHOD=email
```

**Twilio (Required even if using email - for fallback):**
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+0987654321
```

**LLM:**
```
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.2
```

### Optional Variables

```
DB_PATH=/opt/render/project/src/agent_state.db
EMAIL_CHECK_MINUTES=15
MAX_EMAILS_PER_ACCOUNT=10
LOG_LEVEL=INFO
RSS_ENABLED=false
```

## Step 4: Test Deployment

1. After deployment, check the logs in Render dashboard
2. The cron job will run every 15 minutes automatically
3. You can manually trigger a run from Render dashboard if needed

## Important Notes

1. **Database Persistence**: The database file is stored in the project directory. On free tier, this persists between runs but may be cleared if the service is idle for too long.

2. **Environment Variables**: Never commit `.env` file to GitHub. Use Render's environment variables UI.

3. **Email App Passwords**: 
   - Gmail: Generate at https://myaccount.google.com/apppasswords
   - Yahoo: Generate at https://login.yahoo.com/account/security
   - Outlook: Generate app password in account settings

4. **Cron Schedule**: The schedule `*/15 * * * *` runs every 15 minutes. You can change this in Render dashboard.

5. **Logs**: Check logs in Render dashboard → Your Cron Job → Logs tab

## Troubleshooting

### Cron Job Not Running
- Check the schedule is correct in Render dashboard
- Verify the start command is correct
- Check logs for errors

### Authentication Errors
- Verify app passwords are correct
- Check that 2-Step Verification is enabled
- Ensure email addresses match exactly (case-sensitive for some providers)

### Database Issues
- The database path should be writable
- On free tier, database may be cleared after inactivity
- Consider using a persistent volume for production

### Email Not Sending
- Check SMTP settings for `SEND_SUMMARY_FROM_EMAIL`
- Verify the sender email has an app password configured
- Check Render logs for SMTP errors

## Updating the Deployment

1. Push changes to GitHub
2. Render will automatically rebuild on next run
3. Or manually trigger a rebuild from Render dashboard

## Cost

- **Free Tier**: 750 hours/month (enough for a cron job running every 15 minutes)
- **Paid Tier**: Starts at $7/month for more reliability and persistence

