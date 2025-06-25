from fastapi import APIRouter, HTTPException, Header, path
from app.lists.models import UserList, ListItem, CreateItemRequest
from app.supabase_client import supabase
from datetime import datetime
from typing import Optional, List
import os
import requests
from app.utils import *
from pydantic import BaseModel

router = APIRouter()

# ---------------------- Helpers ----------------------------------------- #

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

# -------------------------------------------------------------------------- #
@router.post("/lists")
def create_list(
    user_list: UserList,
    user_id: str,
    token: str = Header(...)
):
    try:
        supabase.postgrest.auth(token)
        now = datetime.utcnow().isoformat()
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
# @router.put("/lists/{list_id}")
# def update_list(list_id: str, user_list: UserList):
#     now = datetime.now().isoformat()
#
#     # fetch owner to get default
#     res = supabase.table("lists").select("user_id").eq("list_id", list_id).single().execute()
#     if not res.data:
#         raise HTTPException(status_code=404, detail="List not found")
#
#     user_id = res.data["user_id"]
#     default_geo = get_profile_geo(user_id)
#
#     list_geo = user_list.geo_alert if user_list.geo_alert is not None else default_geo
#     deadline_str = convert_datetime_to_iso(user_list.deadline)
#
#     # update list header
#     supabase.table("lists").update({
#         "name": user_list.name,
#         "deadline": deadline_str,
#         "geo_alert": list_geo,
#         "last_update": now
#     }).eq("list_id", list_id).execute()
#
#     # soft-delete old items (unchanged)
#     supabase.table("lists_items").update({
#         "is_deleted": True,
#         "deleted_at": now
#     }).eq("list_id", list_id).execute()
#
#     # insert new items
#     items_payload = []
#     for it in user_list.items:
#         item_geo = it.geo_alert if it.geo_alert is not None else list_geo
#         item_deadline_str = convert_datetime_to_iso(it.deadline)
#
#         items_payload.append({
#             "list_id": list_id,
#             "name": it.name,
#             "is_checked": it.is_checked,
#             "checked_at": now if it.is_checked else None,
#             "created_at": now,
#             "deadline": item_deadline_str,
#             "geo_alert": item_geo
#         })
#     supabase.table("lists_items").insert(items_payload).execute()
#
#     return {"message": "List updated"}


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
    now = datetime.utcnow().isoformat()
    supabase.table("lists").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    supabase.table("lists_items").update({"is_deleted": True, "deleted_at": now}).eq("list_id", list_id).execute()
    return {"message": "List deleted"}


# -------------------------------------------------------------------------- #
@router.post("/lists/{list_id}/restore")
def restore_list(list_id: str):
    now = datetime.utcnow().isoformat()
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

        supabase.table("lists").update({
            "deadline": deadline,
            "last_update": datetime.now().isoformat()
        }).eq("list_id", list_id).execute()

        return {"message": "Deadline updated"}
    except Exception as e:
        print("[ERROR update_list_deadline]", e)
        raise HTTPException(500, "Failed to update deadline")
