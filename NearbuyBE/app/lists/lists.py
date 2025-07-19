from fastapi import APIRouter, HTTPException, Header, Path
from lists.models import UserList, ListItem, CreateItemRequest
from supabase_client import supabase
from datetime import datetime
from typing import Optional, List
import os
import requests
from utils import *
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()

# ---------------------- Helpers ----------------------------------------- #

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


def fetch_and_store_recommendations(list_name: str, list_id: int):
    """Fetch recommendations from ML API both per-item and per-list,
    filter out existing items and any suggestions already used/rejected,
    then store the rest."""

    ml_base = os.getenv("ML_API_BASE_URL", "http://localhost:8000")

    # 1) Gather existing list items
    existing_rows = (
        supabase
        .table("lists_items")
        .select("name")
        .eq("list_id", list_id)
        .eq("is_deleted", False)
        .execute()
        .data or []
    )
    existing_names = {r["name"] for r in existing_rows}

    # 2) Pull all suggestions for this list, then preserve those used or rejected
    all_sugs = (
        supabase
        .table("items_suggestions")
        .select("name, used, rejected")
        .eq("list_id", list_id)
        .execute()
        .data or []
    )
    preserved_names = {
        row["name"]
        for row in all_sugs
        if row.get("used") or row.get("rejected")
    }

    # 3) Collect fresh recommendations from the ML service
    recs = set()
    for prod in existing_names:
        try:
            resp = requests.get(
                f"{ml_base}/recommend_similar_products",
                params={"product_name": prod, "top_k": 5},
                timeout=20
            )
            resp.raise_for_status()
            recs.update(resp.json().get("similar_products", []))
        except Exception as e:
            print(f"[ML Error] similar for '{prod}': {e}")

    try:
        resp2 = requests.get(
            f"{ml_base}/recommend_by_list_name",
            params={"list_name": list_name},
            timeout=20
        )
        resp2.raise_for_status()
        recs.update(resp2.json().get("recommended_products", []))
    except Exception as e:
        print(f"[ML Error] by-name for '{list_name}': {e}")

    # 4) Filter out existing items and preserved suggestions
    for item in recs:
        print(item)

    if len(recs) == 0:
        print("nothing here!")

    filtered = [
        item for item in recs
        if item not in existing_names and item not in preserved_names
    ]

    # 5) Delete only the old, still-pending suggestions for this list
    (supabase
        .table("items_suggestions")
        .delete()
        .eq("list_id", list_id)
        .eq("used", False)
        .eq("rejected", False)
        .execute()
    )

    # 6) Insert the new suggestions
    if filtered:
        payload = [{"list_id": list_id, "name": item} for item in filtered]
        supabase.table("items_suggestions").insert(payload).execute()

# -------------------------------------------------------------------------- #
@router.post("/lists")
def create_list(
    user_list: UserList,
    user_id: str,
    token: str = Header(...)
):
    try:
        supabase.postgrest.auth(token)
        now = datetime.now().isoformat()
        default_geo = get_profile_geo(user_id)
        list_geo = user_list.geo_alert if user_list.geo_alert is not None else default_geo
        deadline_str = convert_datetime_to_iso(user_list.deadline)

        res = (
            supabase.table("lists")
            .insert({
                "user_id": user_id,
                "name": user_list.name,
                "created_at": now,
                "last_update": now,
                "deadline": deadline_str,
                "geo_alert": list_geo,
                "pic_path": user_list.pic_path,
            })
            .execute()
        )

        if not res.data:
            raise HTTPException(500, "Insert failed")
        
        list_id = res.data[0]["list_id"]
        # Fetch and store combined ML recommendations
        fetch_and_store_recommendations(user_list.name, list_id)

        return {
            "list_id": list_id,
            "message": "List created with recommendations"
        }

    except Exception as e:
        print("[ERROR create_list]", e)
        raise HTTPException(500, "Failed to create list")


@router.get("/lists")
def get_user_lists(user_id: str, token: str = Header(...)):
    supabase.postgrest.auth(token)
    rows = (
        supabase.table("lists")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_deleted", False)
        .order("last_update", desc=True)
        .execute()
    ).data

    if not rows:
        return { "lists": [], "any_geo_enabled": False }

    out = []
    any_geo = False

    for lst in rows:
        lid = lst["list_id"]
        items = (
            supabase.table("lists_items")
            .select("*")
            .eq("list_id", lid)
            .eq("is_deleted", False)
            .execute()
            .data or []
        )
        suggestions = (
            supabase.table("items_suggestions")
            .select("*")
            .eq("list_id", lid)
            .eq("used", False)
            .eq("rejected", False)
            .execute()
            .data or []
        )

        if lst.get("geo_alert"):
            any_geo = True

        if any(it.get("geo_alert") for it in items):
            any_geo = True

        unchecked_count = sum(
            1 for it in items if not it.get("is_checked", False)
        )

        unchecked = sum(1 for i in items if not i.get("is_checked", False))

        out.append({
            "id": lid,
            "name": lst["name"],
            "deadline": lst["deadline"],
            "geo_alert": lst["geo_alert"],
            "pic_path": lst.get("pic_path"),
            "items": items,
            "unchecked_count": unchecked,
            "suggested_items": suggestions
        })
    return {
        "lists": out,
        "any_geo_enabled": any_geo
    }


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

    try:
        items = (
            supabase.table("lists_items")
            .select("*")
            .eq("list_id", list_id)
            .eq("is_deleted", False)
            .order("is_checked")
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

    # Get lowercase names of existing items for deduplication
    existing_names = {item["name"].strip().lower() for item in items if item.get("name")}

    # Filter out suggestions with duplicate names
    filtered_suggestions = [
        s for s in suggestions if s.get("name", "").strip().lower() not in existing_names
    ]

    return {
        "name": lst["name"],
        "deadline": lst["deadline"],
        "geo_alert": lst["geo_alert"],
        "pic_path": lst.get("pic_path"),
        "items": items,
        "suggestions": filtered_suggestions
    }


# -------------------------------------------------------------------------- #

@router.patch("/lists/{list_id}/name")
def update_list_name(list_id: str, body: dict, token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        name = body.get("name", "").strip()
        if not name:
            raise HTTPException(400, "Invalid name")

        supabase.table("lists").update({
            "name": name,
            "last_update": datetime.now().isoformat(),
        }).eq("list_id", list_id).execute()

        return {"message": "List name updated"}
    except Exception as e:
        print("[ERROR update_list_name]", e)
        raise HTTPException(500, "Failed to update name")


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
    lst = supabase.table("lists").select("*").eq("list_id", list_id).single().execute().data
    if not lst:
        raise HTTPException(404, "List not found")
    if not lst.get("is_deleted", False):
        return {"message": "List is not deleted"}
    deleted_at = datetime.fromisoformat(lst["deleted_at"].replace("Z", "+00:00"))
    if (datetime.now() - deleted_at).days > 30:
        raise HTTPException(status_code=410, detail="Too old to restore")

    supabase.table("lists").update({"is_deleted": False, "deleted_at": None, "last_update": now}).eq("list_id",
                                                                                                     list_id).execute()
    supabase.table("lists_items").update({"is_deleted": False, "deleted_at": None}).eq("list_id", list_id).execute()
    return {"message": "List successfully restored", "list_id": list_id}


# -------------------------------------------------------------------------- #
def create_item_internal(list_id: str, item_name: str, token: str, geo_alert=None, deadline=None) -> dict:
    supabase.postgrest.auth(token)
    now = datetime.now().isoformat()

    payload = {
        "list_id": list_id,
        "name": item_name,
        "is_checked": False,
        "created_at": now,
        "geo_alert": geo_alert,
        "deadline": convert_datetime_to_iso(deadline),
    }

    # Only send non-null values
    payload = {k: v for k, v in payload.items() if v is not None}

    res = (
        supabase.table("lists_items")
        .insert(payload)
        .execute()
    )

    if not res.data:
        raise HTTPException(500, "Insert failed")

    bump_list_timestamp(list_id)

    return {
        "item_id": res.data[0]["item_id"],
        "name": res.data[0]["name"],
    }

@router.post("/lists/{list_id}/items")
def create_item(list_id: str, req: CreateItemRequest, token: str = Header(...)):
    try:
        return create_item_internal(list_id, req.item_name, token,
            geo_alert=req.geo_alert,
            deadline=req.deadline)
    except Exception as e:
        print("[ERROR create_item]", e)
        raise HTTPException(500, "Failed to create item")

@router.post("/lists/{list_id}/suggestions/{suggestion_id}/accept")
def accept_suggestion(
    list_id: str,
    suggestion_id: str,
    req: CreateItemRequest,
    token: str = Header(...)
):
    try:
        supabase.postgrest.auth(token)
        # Create item with provided name
        result = create_item_internal(list_id, req.item_name, token,
            geo_alert=req.geo_alert,
            deadline=req.deadline)

        # Mark suggestion as used
        print(suggestion_id)
        supabase.table("items_suggestions").update({"used": True}).eq("suggestion_id", suggestion_id).execute()

        return {"message": "Suggestion accepted", "item_id": result["item_id"]}

    except Exception as e:
        print("[ERROR accept_suggestion]", e)
        raise HTTPException(500, "Failed to accept suggestion")

@router.post("/lists/{list_id}/suggestions/{suggestion_id}/reject")
def reject_suggestion(suggestion_id: str, token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        supabase.table("items_suggestions").update({"rejected": True}).eq("suggestion_id", suggestion_id).execute()
        return {"message": "Suggestion rejected"}
    except Exception as e:
        print("[ERROR reject_suggestion]", e)
        raise HTTPException(500, "Failed to reject suggestion")


@router.patch("/lists/{list_id}/geo")
def update_list_geo_alert(list_id: str, body: dict, token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        value = body.get("geo_alert")
        if value is None:
            raise HTTPException(400, "geo_alert missing")
        supabase.table("lists").update({
            "geo_alert": value,
            "last_update": datetime.now().isoformat(),
        }).eq("list_id", list_id).execute()

        return {"message": "Geo alert updated"}
    except Exception as e:
        print("[ERROR update_list_geo_alert]", e)
        raise HTTPException(500, "Failed to update geo alert")

@router.patch("/lists/{list_id}/deadline")
def update_list_deadline(list_id: str, body: dict, token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        deadline = body.get("deadline")

        # Fetch current deadline
        res = (
            supabase.table("lists")
            .select("deadline")
            .eq("list_id", list_id)
            .single()
            .execute()
        )
        old_deadline = res.data.get("deadline")
        # old_dt = datetime.fromisoformat(old_deadline).isoformat()

        # Update list deadline
        supabase.table("lists").update({
            "deadline": deadline,
            "deadline_notified": False,
            "last_update": datetime.now().isoformat()
        }).eq("list_id", list_id).execute()

        # Update items in this list that had the old deadline
        if old_deadline:
            supabase.table("lists_items").update({
                "deadline": deadline,
                "deadline_notified": False
            }).eq("list_id", list_id).eq("deadline", old_deadline).execute()

        return {"message": "Deadline updated"}

    except Exception as e:
        print("[ERROR update_list_deadline]", e)
        raise HTTPException(500, "Failed to update deadline")
    

@router.post("/lists/{list_id}/recommendations", status_code=204)
def generate_recommendations_for_list(list_id: UUID):
    list_id_str = str(list_id)
    # 1) look up the list name
    res = supabase.table("lists") \
        .select("name") \
        .eq("list_id", list_id) \
        .single() \
        .execute()

    if not res.data:
        raise HTTPException(404, f"List {list_id} not found")

    list_name = res.data["name"]

    # 2) call your helper
    fetch_and_store_recommendations(list_name, list_id_str)

    # 3) return no-content
    return