from fastapi import APIRouter, HTTPException, Header, Path
from lists.models import UserList, ListItem
from supabase_client import supabase
from datetime import datetime
from typing import List
from pydantic import BaseModel
from utils import *

router = APIRouter()

class UserList(BaseModel):
    name: str
    geo_alert: bool | None = None
    deadline: str | None = None

# ---------- small helper -------------------------------------------------- #

# Does the same as get_profile_geo - Delete later (if not needed)
# def user_has_global_geo_alert(user_id: str) -> bool:
#     """Look at user_profiles.geo_alert once per request."""
#     prof = (
#         supabase.table("user_profiles")
#         .select("geo_alert")
#         .eq("user_id", user_id)
#         .execute()
#     )
#     return bool(prof.data and prof.data.get("geo_alert"))

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
def create_list(
    user_list: UserList,
    user_id: str,
    token: str = Header(...)
):
    try:
        print("GOT HERE 1")
        supabase.postgrest.auth(token)
        now = datetime.now().isoformat()
        print("GOT HERE 2")
        default_geo = get_profile_geo(user_id)
        list_geo = user_list.geo_alert if user_list.geo_alert is not None else default_geo
        deadline_str = convert_datetime_to_iso(user_list.deadline)
        print("GOT HERE 3")

        res = (
            supabase.table("lists")
            .insert({
                "user_id": user_id,
                "name": user_list.name,
                "created_at": now,
                "last_update": now,
                "deadline": deadline_str,
                "geo_alert": list_geo,
            })
            .execute()
        )

        print("GOT HERE 4")
        if not res.data:
            raise HTTPException(500, "Insert failed")

        return {
            "list_id": res.data[0]["list_id"],
            "message": "List created"
        }

    except Exception as e:
        print("[ERROR create_list]", e)
        raise HTTPException(500, "Failed to create list")

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
    try:
        lst = (
            supabase.table("lists")
            .select("*")
            .eq("list_id", list_id)
            .eq("is_deleted", False)
            .single()
            .execute()
            .data
        )

    except Exception as e:
        print("[Generic get_list error]", e)
        raise HTTPException(status_code=500, detail="Failed to get list")

    if not lst:
        raise HTTPException(status_code=404, detail="List not found")

    try:
        items = (
            supabase.table("lists_items")
            .select("*")
            .eq("list_id", list_id)
            .eq("is_deleted", False)
            .execute()
            .data
        )
    except Exception as e:
        print(f"get_list items error: {e}")
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
    now = datetime.now().isoformat()

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
    now = datetime.now().isoformat()
    supabase.table("lists").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    return {"message": "List deleted"}

# -------------------------------------------------------------------------- #
@router.post("/lists/{list_id}/restore")
def restore_list(list_id: str):
    now = datetime.now().isoformat()
    lst = (
        supabase.table("lists").select("*").eq("list_id", list_id).single().execute().data
    )
    if not lst:
        raise HTTPException(status_code=404, detail="List not found")
    if not lst["is_deleted"]:
        return {"message": "List is not deleted"}

    # still within 30 days?
    deleted_at = datetime.fromisoformat(lst["deleted_at"].replace("Z", "+00:00"))
    if (datetime.now() - deleted_at).days > 30:
        raise HTTPException(status_code=410, detail="Too old to restore")

    supabase.table("lists").update({"is_deleted": False, "deleted_at": None, "last_update": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": False, "deleted_at": None}).eq("list_id", list_id).execute()
    return {"message": "List successfully restored", "list_id": list_id}

# -------------------------------------------------------------------------- #
@router.post("/lists/{list_id}/items")
def create_item(
    list_id: str,
    req: CreateItemRequest,
    token: str = Header(...),
):
    item_name = req.item_name
    try:
        supabase.postgrest.auth(token)
        now = datetime.now().isoformat()

        # Fetch list info (geo_alert and user_id)
        list_res = (
            supabase.table("lists")
            .select("geo_alert", "user_id")
            .eq("list_id", list_id)
            .single()
            .execute()
        )
        if not list_res.data:
            raise HTTPException(404, "List not found")

        list_geo = list_res.data["geo_alert"]
        user_id = list_res.data["user_id"]

        # Fetch user's default geo_alert
        user_geo = get_profile_geo(user_id)

        # Final geo_alert decision
        geo_alert = list_geo if list_geo is not None else bool(user_geo)

        # Insert item
        res = (
            supabase.table("lists_items")
            .insert({
                "list_id": list_id,
                "name": item_name,
                "is_checked": False,
                "created_at": now,
                "geo_alert": geo_alert,
            })
            .execute()
        )
        if not res.data:
            raise HTTPException(500, "Insert failed")

        item = res.data[0]
        bump_list_timestamp(list_id)


        return {
            "item_id": item["item_id"],
            "name": item["name"],
        }

    except Exception as e:
        print("[ERROR create_item]", e)
        raise HTTPException(500, "Failed to create item")