import requests
import json

EXPO_PUSH_URL = "to_be_filled"

def send_expo_push(to_token: str, title: str, body: str, data: dict = None) -> bool:
    """
    Send a push notification via Expo's Push API to a single device.
    Returns True if Expo responds with "ok", False otherwise.
    """
    payload = {
        "to": to_token,
        "title": title,
        "body": body,
        # Optionally include a data field for deep link or store details:
        "data": data or {}
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(EXPO_PUSH_URL, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        resp_json = response.json()
        # Expo responds with an array of receipts, but for a single "to", we can check the first:
        if resp_json.get("data") and isinstance(resp_json["data"], list):
            receipt = resp_json["data"][0]
            if receipt.get("status") == "ok":
                return True
            else:
                # Could log receipt.get("message") or errorCodes
                print("🚨 Expo push error receipt:", receipt)
                return False
        # In legacy format, Expo returns {"id": "...", "status": "ok"} for a single push
        if resp_json.get("status") == "ok":
            return True
        print("🚨 Unexpected Expo response:", resp_json)
        return False
    else:
        print(f"🚨 Expo HTTP Error {response.status_code}: {response.text}")
        return False
