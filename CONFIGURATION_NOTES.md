# Configuration Notes

## Email Account Configuration

### Important: Sender vs Monitored Accounts

**Monitored Accounts (`EMAIL_ACCOUNTS`):**
- These are email accounts that the agent will **monitor** (check for incoming emails)
- Emails FROM these accounts are NOT processed (they are the inboxes being checked)
- Example: `EMAIL_ACCOUNTS=account1@gmail.com,account2@outlook.com`

**Sender Account (`SEND_SUMMARY_FROM_EMAIL`):**
- This is the email account used to **send** summary notifications
- This account should NOT be in `EMAIL_ACCOUNTS` (to avoid monitoring your own sent emails)
- You still need to provide the password: `EMAIL_PASSWORD_sender@gmail.com=...`
- Example: `SEND_SUMMARY_FROM_EMAIL=hemsra@gmail.com`

**Sender Filters (`EMAIL_FROM_FILTERS`):**
- If you want to process emails FROM a specific address (like hemsra@gmail.com), add it to filters
- Example: `EMAIL_FROM_FILTERS=hemsra@gmail.com,@linkedin.com`
- This allows you to receive emails from hemsra@gmail.com in other monitored accounts

### Example Configuration

```bash
# Monitor these accounts (check their inboxes)
EMAIL_ACCOUNTS=account1@gmail.com,account2@outlook.com

# Passwords for monitored accounts
EMAIL_PASSWORD_account1@gmail.com=app_password_1
EMAIL_PASSWORD_account2@outlook.com=app_password_2

# Sender account (NOT in EMAIL_ACCOUNTS)
SEND_SUMMARY_FROM_EMAIL=hemsra@gmail.com
EMAIL_PASSWORD_hemsra@gmail.com=app_password_for_hemsra

# If you want to receive emails FROM hemsra@gmail.com in other accounts
EMAIL_FROM_FILTERS=hemsra@gmail.com,@linkedin.com

# Recipient
SEND_SUMMARY_TO_EMAIL=recipient@example.com
```

### Key Points

1. **hemsra@gmail.com should NOT be in `EMAIL_ACCOUNTS`** - it's only used for sending
2. **Keep `EMAIL_PASSWORD_hemsra@gmail.com`** - needed for SMTP authentication
3. **Add to `EMAIL_FROM_FILTERS`** if you want emails from hemsra@gmail.com processed from other accounts

