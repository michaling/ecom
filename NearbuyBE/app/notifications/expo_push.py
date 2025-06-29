import requests
import json
from uuid import UUID
import datetime

EXPO_PUSH_URL = "to_be_filled"


def _serialize_for_json(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def _serialize_uuid(obj):
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {obj.__class__.__name__} not serializable")
"""

def send_expo_push(to_token: str, title: str, body: str, data: dict = None) -> bool:
    # Send a push notification via Expo's Push API to a single device.
    # Returns True if Expo responds with "ok", False otherwise.
    # Converts any UUIDs in `data` to strings so payload is JSON-serializable.
    # Ensure data values are JSON-compatible (cast UUIDs to str)
    clean_data = {}
    if data:
        for key, value in data.items():
            if isinstance(value, UUID):
                clean_data[key] = str(value)
            else:
                clean_data[key] = value

    payload = {
        "to": to_token,
        "title": title,
        "body": body,
        "data": clean_data
    }
    headers = {
        "Content-Type": "application/json"
    }

    # Use json.dumps with default=_serialize_uuid just in case nested UUIDs appear
    raw = json.dumps(payload, default=_serialize_uuid)
    response = requests.post(EXPO_PUSH_URL, headers=headers, data=raw)

    if response.status_code == 200:
        resp_json = response.json()
        # Check new format: {"data":[{"status":"ok",...}]}
        if resp_json.get("data") and isinstance(resp_json["data"], list):
            receipt = resp_json["data"][0]
            if receipt.get("status") == "ok":
                return True
            else:
                print("🚨 Expo push error receipt:", receipt)
                return False
        # Legacy: {"id":"...", "status":"ok"}
        if resp_json.get("status") == "ok":
            return True
        print("🚨 Unexpected Expo response:", resp_json)
        return False
    else:
        print(f"🚨 Expo HTTP Error {response.status_code}: {response.text}")
        return False
"""
# mock for testing


def send_expo_push(to_token: str, title: str, body: str, data: dict = None) -> bool:
    # MOCKED push sender: print the payload instead of POSTing.
    # Converts any UUIDs in `data` → strings so json.dumps won’t fail.
    payload = {
        "to": to_token,
        "title": title,
        "body": body,
        "data": {}
    }
    if data:
        # Walk through data and cast any UUIDs to str
        clean_data = {}
        for k, v in data.items():
            if isinstance(v, UUID):
                clean_data[k] = str(v)
            else:
                clean_data[k] = v
        payload["data"] = clean_data

    # Now payload is guaranteed JSON‐serializable (assuming no other exotic types)
    print("\n=== MOCK EXPO PUSH ===")
    print(json.dumps(payload, indent=2, default=_serialize_for_json))
    print("=== END MOCK ===\n")
    return True
