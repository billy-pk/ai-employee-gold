"""
Setup Gmail OAuth tokens for both reading and sending.
Run this whenever tokens expire or need to be refreshed.
"""
import pickle
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES_READ = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES_SEND = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]

CREDS_PATH = Path('credentials/gmail_credentials.json')
TOKEN_READ = Path('credentials/token.pickle')
TOKEN_SEND = Path('credentials/token_send.pickle')


def refresh_or_reauth(token_path: Path, scopes: list, label: str) -> bool:
    creds = None
    if token_path.exists():
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)

    if creds and creds.valid:
        print(f"[{label}] Token is still valid — no action needed.")
        return True

    if creds and creds.expired and creds.refresh_token:
        print(f"[{label}] Token expired — attempting silent refresh...")
        try:
            creds.refresh(Request())
            with open(token_path, 'wb') as f:
                pickle.dump(creds, f)
            print(f"[{label}] Token refreshed successfully.")
            return True
        except Exception as e:
            print(f"[{label}] Silent refresh failed ({e}), starting browser auth...")

    if not CREDS_PATH.exists():
        print(f"ERROR: {CREDS_PATH} not found. Download it from Google Cloud Console.")
        return False

    print(f"[{label}] Opening browser for authorization...")
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), scopes)
    creds = flow.run_local_server(port=0)
    with open(token_path, 'wb') as f:
        pickle.dump(creds, f)
    print(f"[{label}] Token saved to {token_path}")
    return True


def main():
    os.chdir(Path(__file__).parent.parent)
    print("=== Gmail Auth Setup ===\n")

    ok_read = refresh_or_reauth(TOKEN_READ, SCOPES_READ, "READ ")
    print()
    ok_send = refresh_or_reauth(TOKEN_SEND, SCOPES_SEND, "SEND ")

    print("\n=== Summary ===")
    print(f"  Read token:  {'✅ OK' if ok_read else '❌ FAILED'}")
    print(f"  Send token:  {'✅ OK' if ok_send else '❌ FAILED'}")

    if ok_read and ok_send:
        print("\nAll tokens ready. Your AI Employee can read and send emails.")
    else:
        print("\nSome tokens failed. Check errors above.")


if __name__ == '__main__':
    main()
