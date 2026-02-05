# Gmail API Credentials Setup

This folder stores OAuth 2.0 credentials for the Gmail API. **Never commit actual credential files to Git.**

## Setup Instructions

### 1. Enable Gmail API in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Library**
4. Search for "Gmail API" and click **Enable**

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in app name (e.g., "AI Employee")
   - Add your email as developer contact
   - Add scopes: `gmail.readonly`
   - Add your Gmail address as a test user
4. Choose application type: **Desktop app**
5. Name it (e.g., "AI Employee Gmail Watcher")
6. Click **Create**

### 3. Download Credentials

1. Click the **Download** button (⬇️) next to your newly created OAuth client
2. Save the downloaded JSON file as `gmail_credentials.json` in this `credentials/` folder
3. The file should be located at: `~/vibe-coding-projects/ai-employee/credentials/gmail_credentials.json`

### 4. Required OAuth Scopes

For Bronze phase, only readonly scope is needed:
- `https://www.googleapis.com/auth/gmail.readonly`

For future phases (Silver/Gold), you may need:
- `https://www.googleapis.com/auth/gmail.modify` (mark as read, archive)
- `https://www.googleapis.com/auth/gmail.send` (send emails)

### 5. First Run Authentication

On first run of the Gmail Watcher:
1. A browser window will open
2. Sign in with your Google account
3. Grant the requested permissions
4. A `token.pickle` file will be created automatically
5. Future runs will use the cached token

## Files in This Directory

- `gmail_credentials.json` - OAuth 2.0 client credentials (download from Google Cloud)
- `token.pickle` - Cached authentication token (auto-generated on first run)
- `.gitkeep` - Keeps this folder in Git while ignoring contents
- `README.md` - This file

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `gmail_credentials.json` to Git
- Never commit `token.pickle` to Git
- Never share these files publicly
- The `.gitignore` file is configured to exclude all `.json` and `.pkl` files

## Troubleshooting

### "File not found: gmail_credentials.json"
- Make sure you've downloaded the credentials from Google Cloud Console
- Verify the file is in this `credentials/` directory
- Check the filename matches exactly: `gmail_credentials.json`

### "Access blocked: This app's request is invalid"
- Make sure you've added your email as a test user in the OAuth consent screen
- Verify the Gmail API is enabled in your project
- Check that the scopes match what you configured

### "Token has been expired or revoked"
- Delete `token.pickle` and re-authenticate
- Check if you revoked access in your Google Account settings

## References

- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Gmail API Scopes](https://developers.google.com/gmail/api/auth/scopes)
