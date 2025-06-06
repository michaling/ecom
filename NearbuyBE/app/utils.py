from supabase_client import supabase
from fastapi import HTTPException
from datetime import datetime

# Update the list's last_update column
def bump_list_timestamp(list_id: str):
    try:
        supabase.table("lists").update({
            "last_update": datetime.now().isoformat()
        }).eq("list_id", list_id).execute()
    except Exception as e:
        print("[ERROR bump_list_timestamp]", e)
        raise HTTPException(status_code=500, detail="Failed to update list timestamp")