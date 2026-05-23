# Credentials Setup

This folder stores API credentials for all integrations. **Never commit credential files to Git.**

## Files in This Directory

| File | Purpose | Auto-generated? |
|------|---------|-----------------|
| `gmail_credentials.json` | Gmail OAuth 2.0 client credentials | No — download from Google Cloud |
| `token.pickle` | Cached Gmail OAuth token | Yes — created on first run |
| `token_send.pickle` | Cached Gmail send-scoped token | Yes — created on first run |
| `twitter_credentials.json` | Twitter/X API keys | No — create manually (see below) |
| `odoo_config.json` | Odoo server connection settings | No — create manually (see below) |

## Security Notes

**IMPORTANT:** Never commit any of these files to Git.
- The `.gitignore` is configured to exclude `.json` and `.pkl` files in this folder
- Never share these files publicly or paste them into chat/issues

---

## Gmail Setup

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create or select a project
2. Navigate to **APIs & Services > Library**, search for "Gmail API", click **Enable**

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **+ CREATE CREDENTIALS > OAuth client ID**
3. Configure the OAuth consent screen if prompted:
   - User type: **External**
   - App name: e.g., `AI Employee`
   - Add your Gmail address as a **test user**
4. Application type: **Desktop app**
5. Click **Create**

### 3. Download and Save

1. Click the Download button next to your new OAuth client
2. Save the file as `credentials/gmail_credentials.json`

### 4. OAuth Scopes Used

| Scope | Purpose |
|-------|---------|
| `gmail.readonly` | Read and list emails (Gmail Watcher) |
| `gmail.send` | Send email replies (Approval Executor) |

### 5. First Run Authentication

On first run of the Gmail Watcher, a browser window opens automatically:
1. Sign in with your Google account
2. Grant the requested permissions
3. `token.pickle` (read) and `token_send.pickle` (send) are saved automatically
4. Future runs use the cached tokens — no browser needed

### Troubleshooting

**"File not found: gmail_credentials.json"**
- Verify you downloaded the file from Google Cloud Console and saved it with exactly that filename

**"Access blocked: This app's request is invalid"**
- Add your Gmail address as a test user in the OAuth consent screen
- Verify the Gmail API is enabled in your Google Cloud project

**"Token has been expired or revoked"**
- Run `uv run python scripts/setup_gmail_auth.py` from the project root — it silently refreshes both tokens, and opens a browser only if the refresh token itself has expired
- As a last resort, delete `token.pickle` and/or `token_send.pickle` manually and re-run the script to force a full re-authorization
- Check that you haven't revoked access in your Google Account security settings

**Refreshing tokens separately**
- `token.pickle` is used by the Gmail Watcher (reading emails)
- `token_send.pickle` is used by the Approval Executor (sending replies)
- Both are refreshed by `scripts/setup_gmail_auth.py` in a single run

---

## Twitter/X Setup

### 1. Create a Developer App

1. Go to [developer.twitter.com](https://developer.twitter.com/) and sign in
2. Create a **Project** and an **App** inside it
3. Under your app's settings, set **App permissions** to **Read and Write** (not read-only)

### 2. Generate Keys and Tokens

Under your app's **Keys and Tokens** tab, generate:

| Field | Where to find it |
|-------|-----------------|
| API Key | "Consumer Keys" section |
| API Secret | "Consumer Keys" section |
| Bearer Token | "Bearer Token" section |
| Access Token | "Authentication Tokens" section |
| Access Token Secret | "Authentication Tokens" section |

> After changing app permissions, regenerate your Access Token & Secret — old tokens keep the old permission level.

### 3. Save to File

Create `credentials/twitter_credentials.json`:

```json
{
  "api_key": "YOUR_API_KEY",
  "api_secret": "YOUR_API_SECRET",
  "access_token": "YOUR_ACCESS_TOKEN",
  "access_token_secret": "YOUR_ACCESS_TOKEN_SECRET",
  "bearer_token": "YOUR_BEARER_TOKEN"
}
```

### Troubleshooting

**"Unauthorized" or 403 Forbidden**
- Confirm app permissions are set to **Read and Write** in the developer portal
- Regenerate your Access Token & Secret after changing permissions

**Tweets not posting after approval**
- Confirm `approved: true` is in the frontmatter of the `Pending_Approval/TWEET_*.md` file
- Check the Approval Executor log: `tail -f /tmp/*.log | grep -i tweet`

---

## Odoo Setup

`odoo_config.json` stores the connection details for your local Odoo instance:

```json
{
  "url": "http://localhost:8069",
  "db": "odoo",
  "username": "admin",
  "password": "admin"
}
```

Adjust `db`, `username`, and `password` to match your Odoo instance. Start Odoo with `docker-compose up -d`.

---

## References

- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Gmail API Scopes](https://developers.google.com/gmail/api/auth/scopes)
- [Twitter API v2 Authentication](https://developer.twitter.com/en/docs/authentication/overview)
