import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from uuid import UUID

# ─── CONFIGURE THESE ──────────────────────────────────────────────────────────
# Path to the service-account JSON you downloaded from GCP
SA_JSON = "../../NearBuyFE/firebase-service-account.json"
# Your Firebase project ID (from Firebase Console → Project settings → General)
PROJECT_ID = "nearbuy-b2480"
FCM_V1_URL = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
# ──────────────────────────────────────────────────────────────────────────────


def _get_fcm_access_token() -> str:
    """Mint an OAuth2 access token for FCM v1."""
    scopes = ["https://www.googleapis.com/auth/firebase.messaging"]
    creds = service_account.Credentials.from_service_account_file(
        SA_JSON, scopes=scopes
    )
    creds.refresh(Request())
    return creds.token


def send_expo_push(to_token: str, title: str, body: str, data: dict = None) -> bool:
    """
    Send a push notification via FCM HTTP v1.
    Returns True on success, False otherwise.
    """
    # Convert any UUIDs to strings
    clean_data = {}
    if data:
        for key, value in data.items():
            clean_data[key] = str(value) if isinstance(value, UUID) else value

    # Build the FCM message payload
    message = {
        "token": to_token,
        "notification": {"title": title, "body": body},
        "data": clean_data,
    }

    # Mint a fresh OAuth2 token
    access_token = _get_fcm_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    # Wrap under top-level "message" as required by HTTP v1
    payload = {"message": message}
    resp = requests.post(FCM_V1_URL, headers=headers, json=payload)

    if resp.status_code == 200:
        return True

    print("🚨 FCM v1 push failed:", resp.status_code, resp.text)
    return False
