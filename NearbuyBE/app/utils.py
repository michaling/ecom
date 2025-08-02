from supabase_client import supabase
from fastapi import HTTPException
from datetime import datetime
import socket


def get_local_ip():
    """Returns the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return "127.0.0.1"


# Update the list's last_update column
def bump_list_timestamp(list_id: str):
    try:
        supabase.table("lists").update({"last_update": datetime.now().isoformat()}).eq(
            "list_id", list_id
        ).execute()
    except Exception as e:
        print("[ERROR bump_list_timestamp]", e)
        raise HTTPException(status_code=500, detail="Failed to update list timestamp")
