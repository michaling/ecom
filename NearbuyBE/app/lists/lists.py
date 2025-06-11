from fastapi import APIRouter, HTTPException, Header
from app.lists.models import UserList
from app.supabase_client import supabase
from datetime import datetime
from typing import Optional
import os
import requests

router = APIRouter()

# ---------------------- Helpers ----------------------------------------- #

def get_profile_geo(user_id: str) -> bool:
    """Return the user-level default (TRUE/FALSE)."""
    res = (
        supabase.table("user_profiles")
        .select("geo_alert")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not res.data or res.data.get("geo_alert") is None:
        return False
    return bool(res.data["geo_alert"])


def convert_datetime_to_iso(value: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string, or pass through None."""
    if value is None:
        return None
    return value.isoformat()


def fetch_and_store_recommendations(list_name: str, list_id: int):
    """Fetch recommendations from ML API both per-item and per-list, filter out existing items, and store them."""
    ml_base = os.getenv("ML_API_BASE_URL", "http://localhost:8000")
    # 1) Gather existing list items
    existing_rows = (
        supabase.table("lists_items")
        .select("name")
        .eq("list_id", list_id)
        .eq("is_deleted", False)
        .execute()
        .data or []
    )
    existing_names = {row["name"] for row in existing_rows}

    # 2) Collect recommendations from similar-products endpoint
    recs = set()
    for prod in existing_names:
        try:
            r = requests.get(
                f"{ml_base}/recommend_similar_products",
                params={"product_name": prod, "top_k": 5},
                timeout=5
            )
            r.raise_for_status()
            sims = r.json().get("similar_products", [])
            recs.update(sims)
        except Exception as e:
            print(f"[ML Error] similar for '{prod}': {e}")

    # 3) Also fetch recommendations by list name
    try:
        r2 = requests.get(
            f"{ml_base}/recommend_by_list_name",
            params={"list_name": list_name},
            timeout=5
        )
        r2.raise_for_status()
        by_name = r2.json().get("recommended_products", [])
        recs.update(by_name)
    except Exception as e:
        print(f"[ML Error] by-name for '{list_name}': {e}")

    # 4) Filter out any items already present and ensure no duplicates
    filtered = list(recs - existing_names)

    # 5) Clear old suggestions
    supabase.table("items_suggestions").delete().eq("list_id", list_id).execute()

    # 6) Insert new suggestions
    payload = [{"list_id": list_id, "suggestion_text": item} for item in filtered]
    if payload:
        supabase.table("items_suggestions").insert(payload).execute()


# --------------------- API Endpoints ------------------------------------ #

@router.post("/lists")
def create_list(user_id: str, user_list: UserList):
    now = datetime.utcnow().isoformat()

    default_geo = get_profile_geo(user_id)
    list_geo = user_list.geo_alert if user_list.geo_alert is not None else default_geo
    deadline = convert_datetime_to_iso(user_list.deadline)

    # Insert list
    res = supabase.table("lists").insert({
        "user_id": user_id,
        "name": user_list.name,
        "created_at": now,
        "last_update": now,
        "deadline": deadline,
        "geo_alert": list_geo
    }).execute()
    if not res.data:
        raise HTTPException(500, "Failed to insert list")
    list_id = res.data[0]["list_id"]

    # Insert items
    items_payload = []
    for item in user_list.items:
        items_payload.append({
            "list_id": list_id,
            "name": item.name,
            "is_checked": item.is_checked,
            "checked_at": now if item.is_checked else None,
            "created_at": now,
            "deadline": convert_datetime_to_iso(item.deadline),
            "geo_alert": item.geo_alert if item.geo_alert is not None else list_geo
        })
    if items_payload:
        supabase.table("lists_items").insert(items_payload).execute()

    # Fetch and store combined ML recommendations
    fetch_and_store_recommendations(user_list.name, list_id)

    return {"list_id": list_id, "message": "List created with recommendations"}

@router.get("/lists")
def get_user_lists(user_id: str, token: str = Header(...)):
    supabase.postgrest.auth(token)
    rows = (
        supabase.table("lists")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_deleted", False)
        .execute()
        .data or []
    )

    out = []
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
        unchecked = sum(1 for i in items if not i.get("is_checked", False))
        out.append({
            "id": lid,
            "name": lst["name"],
            "deadline": lst["deadline"],
            "geo_alert": lst["geo_alert"],
            "items": items,
            "unchecked_count": unchecked,
            "suggested_items": suggestions
        })
    return out

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
        raise HTTPException(404, "List not found")

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

@router.put("/lists/{list_id}")
def update_list(list_id: str, user_list: UserList):
    now = datetime.utcnow().isoformat()
    res = supabase.table("lists").select("user_id").eq("list_id", list_id).single().execute()
    if not res.data:
        raise HTTPException(404, "List not found")
    default_geo = get_profile_geo(res.data["user_id"])
    list_geo = user_list.geo_alert if user_list.geo_alert is not None else default_geo
    deadline = convert_datetime_to_iso(user_list.deadline)

    supabase.table("lists").update({
        "name": user_list.name,
        "deadline": deadline,
        "geo_alert": list_geo,
        "last_update": now
    }).eq("list_id", list_id).execute()

    supabase.table("lists_items").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()

    items_payload = []
    for item in user_list.items:
        items_payload.append({
            "list_id": list_id,
            "name": item.name,
            "is_checked": item.is_checked,
            "checked_at": now if item.is_checked else None,
            "created_at": now,
            "deadline": convert_datetime_to_iso(item.deadline),
            "geo_alert": item.geo_alert if item.geo_alert is not None else list_geo
        })
    if items_payload:
        supabase.table("lists_items").insert(items_payload).execute()

    return {"message": "List updated"}

@router.delete("/lists/{list_id}")
def delete_list(list_id: str):
    now = datetime.utcnow().isoformat()
    supabase.table("lists").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    return {"message": "List deleted"}

@router.post("/lists/{list_id}/restore")
def restore_list(list_id: str):
    now = datetime.utcnow().isoformat()
    lst = supabase.table("lists").select("*").eq("list_id", list_id).single().execute().data
    if not lst:
        raise HTTPException(404, "List not found")
    if not lst.get("is_deleted", False):
        return {"message": "List is not deleted"}
    deleted_at = datetime.fromisoformat(lst["deleted_at"].replace("Z", "+00:00"))
    if (datetime.utcnow() - deleted_at).days > 30:
        raise HTTPException(410, "Too old to restore")
    supabase.table("lists").update({"is_deleted": False, "deleted_at": None, "last_update": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": False, "deleted_at": None}).eq("list_id", list_id).execute()
    return {"message": "List successfully restored", "list_id": list_id}
