from fastapi import FastAPI, HTTPException
from models import UserList, ListItem
from supabase_client import supabase
from datetime import datetime
from typing import List

app = FastAPI()

# ---------- small helper -------------------------------------------------- #
def user_has_global_geo_alert(user_id: str) -> bool:
    """Look at user_profiles.geo_alert once per request."""
    prof = (
        supabase.table("user_profiles")
        .select("geo_alert")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return bool(prof.data and prof.data.get("geo_alert"))

# -------------------------------------------------------------------------- #
@app.post("/lists/")
def create_list(user_id: str, user_list: UserList):
    now = datetime.utcnow().isoformat()

    force_geo = user_has_global_geo_alert(user_id)
    list_geo   = True if force_geo else user_list.geo_alert

    # Convert deadline to ISO string if it's a datetime object
    deadline_str = None
    if user_list.deadline:
        if isinstance(user_list.deadline, datetime):
            deadline_str = user_list.deadline.isoformat()
        else:
            deadline_str = user_list.deadline

    # ---------- insert list ------------------------------------------------ #
    list_payload = {
        "user_id": user_id,
        "name": user_list.name,
        "created_at": now,
        "last_update": now,
        "is_deleted": False,
        "deadline": deadline_str,
        "geo_alert": list_geo
    }
    list_res = supabase.table("lists").insert(list_payload).execute()
    if not list_res.data or not list_res.data[0].get("list_id"):
        raise HTTPException(status_code=500, detail="Failed to insert list")
    list_id = list_res.data[0]["list_id"]

    # ---------- insert items ---------------------------------------------- #
    items = []
    for item in user_list.items:
        item_geo = True if force_geo else item.geo_alert
        
        # Convert item deadline to ISO string if it's a datetime object
        item_deadline_str = None
        if item.deadline:
            if isinstance(item.deadline, datetime):
                item_deadline_str = item.deadline.isoformat()
            else:
                item_deadline_str = item.deadline
        
        items.append({
            "list_id": list_id,
            "name": item.name,
            "is_checked": item.is_checked,
            "checked_at": now if item.is_checked else None,
            "created_at": now,
            "is_deleted": False,
            "deadline": item_deadline_str,
            "geo_alert": item_geo
        })
    supabase.table("lists_items").insert(items).execute()
    return {"list_id": list_id, "message": "List created"}

# -------------------------------------------------------------------------- #
@app.get("/lists/")
def get_user_lists(user_id: str):
    rows = (
        supabase.table("lists")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_deleted", False)
        .execute()
    ).data

    if not rows:
        return []

    out = []
    for lst in rows:
        items = (
            supabase.table("lists_items")
            .select("*")
            .eq("list_id", lst["list_id"])
            .eq("is_deleted", False)
            .execute()
            .data
            or []
        )
        out.append({
            "id": lst["list_id"],
            "name": lst["name"],
            "deadline": lst["deadline"],
            "geo_alert": lst["geo_alert"],        # NEW ❹
            "items": items
        })
    return out

# -------------------------------------------------------------------------- #
@app.get("/lists/{list_id}")
def get_list(list_id: str):
    lst = (
        supabase.table("lists")
        .select("*")
        .eq("list_id", list_id)
        .eq("is_deleted", False)
        .single()
        .execute()
        .data
    )
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    items = (
        supabase.table("lists_items")
        .select("*")
        .eq("list_id", list_id)
        .eq("is_deleted", False)
        .execute()
        .data
    )
    return {
        "name": lst["name"],
        "deadline": lst["deadline"],
        "geo_alert": lst["geo_alert"],            # NEW ❹
        "items": items
    }

# -------------------------------------------------------------------------- #
@app.put("/lists/{list_id}")
def update_list(list_id: str, user_list: UserList):
    now = datetime.utcnow().isoformat()

    # must we force geo_alert?
    list_row = (
        supabase.table("lists").select("user_id").eq("list_id", list_id).single().execute().data
    )
    if not list_row:
        raise HTTPException(status_code=404, detail="List not found")
    user_id   = list_row["user_id"]
    force_geo = user_has_global_geo_alert(user_id)
    list_geo  = True if force_geo else user_list.geo_alert

    # Convert deadline to ISO string if it's a datetime object
    deadline_str = None
    if user_list.deadline:
        if isinstance(user_list.deadline, datetime):
            deadline_str = user_list.deadline.isoformat()
        else:
            deadline_str = user_list.deadline

    # ---------- update list ----------------------------------------------- #
    supabase.table("lists").update({
        "name": user_list.name,
        "last_update": now,
        "deadline": deadline_str,
        "geo_alert": list_geo
    }).eq("list_id", list_id).execute()

    # ---------- replace items --------------------------------------------- #
    supabase.table("lists_items").update({
        "is_deleted": True,
        "deleted_at": now
    }).eq("list_id", list_id).execute()

    new_items = []
    for item in user_list.items:
        item_geo = True if force_geo else item.geo_alert
        
        # Convert item deadline to ISO string if it's a datetime object
        item_deadline_str = None
        if item.deadline:
            if isinstance(item.deadline, datetime):
                item_deadline_str = item.deadline.isoformat()
            else:
                item_deadline_str = item.deadline
        
        new_items.append({
            "list_id": list_id,
            "name": item.name,
            "is_checked": item.is_checked,
            "checked_at": now if item.is_checked else None,
            "created_at": now,
            "is_deleted": False,
            "deadline": item_deadline_str,
            "geo_alert": item_geo                     # NEW ❸
        })
    supabase.table("lists_items").insert(new_items).execute()
    return {"message": "List updated"}

# -------------------------------------------------------------------------- #
@app.delete("/lists/{list_id}")
def delete_list(list_id: str):
    now = datetime.utcnow().isoformat()
    supabase.table("lists").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    return {"message": "List deleted"}

# -------------------------------------------------------------------------- #
@app.post("/lists/{list_id}/restore")
def restore_list(list_id: str):
    now = datetime.utcnow().isoformat()
    lst = (
        supabase.table("lists").select("*").eq("list_id", list_id).single().execute().data
    )
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    if not lst["is_deleted"]:
        return {"message": "List is not deleted"}

    # still within 30 days?
    deleted_at = datetime.fromisoformat(lst["deleted_at"].replace("Z", "+00:00"))
    if (datetime.utcnow() - deleted_at).days > 30:
        raise HTTPException(status_code=410, detail="Too old to restore")

    supabase.table("lists").update({"is_deleted": False, "deleted_at": None, "last_update": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": False, "deleted_at": None}).eq("list_id", list_id).execute()
    return {"message": "List successfully restored", "list_id": list_id}