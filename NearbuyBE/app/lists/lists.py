from fastapi import APIRouter, HTTPException, Header, Path
from app.lists.models import UserList, ListItem
from app.supabase_client import supabase
from datetime import datetime
from typing import List

router = APIRouter()

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

def get_profile_geo(user_id: str) -> bool:
    """Return the user-level default (TRUE/FALSE)."""
    res = (supabase.table("user_profiles")
                    .select("geo_alert")
                    .eq("user_id", user_id)
                    .single()
                    .execute())
    # Handle case where profile might not exist or geo_alert is None
    if not res.data or res.data.get("geo_alert") is None:
        return False
    return bool(res.data["geo_alert"])

def convert_datetime_to_iso(value):
    """Convert datetime object to ISO string if needed."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value

# -------------------------------------------------------------------------- #
@router.post("/lists")
def create_list(user_id: str, user_list: UserList):
    now = datetime.utcnow().isoformat()

    # 1️⃣  default comes from profile
    default_geo = get_profile_geo(user_id)

    # 2️⃣  list-level value:  explicit > default
    list_geo = user_list.geo_alert if user_list.geo_alert is not None else default_geo

    # Convert deadline to ISO string if it's a datetime object
    deadline_str = convert_datetime_to_iso(user_list.deadline)

    # insert list ---------------------------------------------------------
    list_res = (supabase.table("lists")
                  .insert({
                      "user_id": user_id,
                      "name": user_list.name,
                      "created_at": now,
                      "last_update": now,
                      "deadline": deadline_str,
                      "geo_alert": list_geo        # ⬅ save it
                  })
                  .execute())

    if not list_res.data:
        raise HTTPException(500, "Failed to insert list")

    list_id = list_res.data[0]["list_id"]

    # items ---------------------------------------------------------------
    items_payload = []
    for it in user_list.items:
        item_geo = it.geo_alert if it.geo_alert is not None else list_geo
        item_deadline_str = convert_datetime_to_iso(it.deadline)
        
        items_payload.append({
            "list_id":      list_id,
            "name":         it.name,
            "is_checked":   it.is_checked,
            "checked_at":   now if it.is_checked else None,
            "created_at":   now,
            "deadline":     item_deadline_str,
            "geo_alert":    item_geo,
        })

    supabase.table("lists_items").insert(items_payload).execute()

    return {"list_id": list_id, "message": "List created"}

# -------------------------------------------------------------------------- #
@router.get("/lists")
def get_user_lists(user_id: str,
                   token: str = Header(...)):
    # Authorize user session for RLS
    supabase.postgrest.auth(token)

    print(f"user_id: {user_id}")
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
        list_id = lst["list_id"]

        items = (
            supabase.table("lists_items")
            .select("*")
            .eq("list_id", list_id)
            .eq("is_deleted", False)
            .execute()
            .data
            or []
        )

        unchecked_count = sum(
            1 for it in items if not it.get("is_checked", False)
        )

        out.append({
            "id": list_id,
            "name": lst["name"],
            "deadline": lst["deadline"],
            "geo_alert": lst["geo_alert"],
            "items": items,
            # "unchecked_items": unchecked_items, # Delete Later
            "unchecked_count": unchecked_count
        })

        #print(f"out: {out}")
    return out

# -------------------------------------------------------------------------- #
@router.get("/lists/{list_id}")
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

    suggestions = (
        supabase.table("items_suggestions")
        .select("*")
        .eq("list_id", list_id)
        .eq("used", False)
        .eq("rejected", False)
        .execute()
        .data or []
    )

    return {
        "name": lst["name"],
        "deadline": lst["deadline"],
        "geo_alert": lst["geo_alert"],
        "items": items,
        "suggestions": suggestions
    }

# -------------------------------------------------------------------------- #
@router.put("/lists/{list_id}")
def update_list(list_id: str, user_list: UserList):
    now = datetime.utcnow().isoformat()

    # fetch owner to get default
    res = supabase.table("lists").select("user_id").eq("list_id", list_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="List not found")
    
    user_id = res.data["user_id"]
    default_geo = get_profile_geo(user_id)

    list_geo = user_list.geo_alert if user_list.geo_alert is not None else default_geo
    deadline_str = convert_datetime_to_iso(user_list.deadline)

    # update list header
    supabase.table("lists").update({
        "name":        user_list.name,
        "deadline":    deadline_str,
        "geo_alert":   list_geo,
        "last_update": now
    }).eq("list_id", list_id).execute()

    # soft-delete old items (unchanged)
    supabase.table("lists_items").update({
        "is_deleted": True,
        "deleted_at": now
    }).eq("list_id", list_id).execute()

    # insert new items
    items_payload = []
    for it in user_list.items:
        item_geo = it.geo_alert if it.geo_alert is not None else list_geo
        item_deadline_str = convert_datetime_to_iso(it.deadline)
        
        items_payload.append({
            "list_id":    list_id,
            "name":       it.name,
            "is_checked": it.is_checked,
            "checked_at": now if it.is_checked else None,
            "created_at": now,
            "deadline":   item_deadline_str,
            "geo_alert":  item_geo
        })
    supabase.table("lists_items").insert(items_payload).execute()

    return {"message": "List updated"}



# -------------------------------------------------------------------------- #
@router.delete("/lists/{list_id}")
def delete_list(list_id: str):
    now = datetime.utcnow().isoformat()
    supabase.table("lists").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    return {"message": "List deleted"}

# -------------------------------------------------------------------------- #
@router.post("/lists/{list_id}/restore")
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