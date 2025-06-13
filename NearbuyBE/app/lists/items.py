from fastapi import APIRouter, HTTPException, Header
from supabase_client import supabase
from datetime import datetime
from pydantic import BaseModel
from utils import *
from lists.models import RenameItemRequest, CheckItemRequest, DeleteItemRequest, UpdateItemGeoAlertRequest, UpdateItemDeadlineRequest

router = APIRouter()

# --- Check or uncheck item ---
@router.patch("/items/{item_id}/check")
def check_item(
        item_id: str,
        req: CheckItemRequest,
        token: str = Header(...),
):
    try:
        supabase.postgrest.auth(token)
        now = datetime.now().isoformat()
        res = (
            supabase.table("lists_items")
            .update({
                "is_checked": req.is_checked,
                "checked_at": now if req.is_checked else None,
            })
            .eq("item_id", item_id)
            .execute()
        )

        if not res.data:
            raise HTTPException(status_code=404, detail="Item not found")

        bump_list_timestamp(req.list_id)
        return {"message": "Item checked/unchecked", "item_id": item_id}

    except Exception as e:
        print("[ERROR check_item]", e)
        raise HTTPException(status_code=500, detail="Failed to update check status")


# --- Rename item ---
@router.patch("/items/{item_id}/name")
def rename_item(
        item_id: str,
        req: RenameItemRequest,
        token: str = Header(...),
):
    try:
        supabase.postgrest.auth(token)

        res = (
            supabase.table("lists_items")
            .update({"name": req.name})
            .eq("item_id", item_id)
            .execute()
        )

        if not res.data:
            raise HTTPException(404, "Item not found or not authorised")

        bump_list_timestamp(req.list_id)

        return {"message": "Item renamed", "item_id": item_id}

    except Exception as e:
        print("[ERROR rename_item]", e)
        raise HTTPException(500, "Failed to rename item")


# --- Soft delete ---
@router.delete("/items/{item_id}")
def delete_item(
        item_id: str,
        req: DeleteItemRequest,
        token: str = Header(...),
):
    try:
        supabase.postgrest.auth(token)
        now = datetime.now().isoformat()
        res = (
            supabase.table("lists_items")
            .update({"is_deleted": True, "deleted_at": now})
            .eq("item_id", item_id)
            .execute()
        )

        if not res.data:
            raise HTTPException(404, "Item not found or not authorised")

        bump_list_timestamp(req.list_id)
        return {"message": "Item deleted", "item_id": item_id}

    except Exception as e:
        print("[ERROR delete_item]", e)
        raise HTTPException(500, "Failed to delete item")


@router.patch("/items/{item_id}/geo")
def update_item_geo_alert(
    item_id: str,
    req: UpdateItemGeoAlertRequest,
    token: str = Header(...),
):
    try:
        supabase.postgrest.auth(token)

        res = supabase.table("lists_items").update({
            "geo_alert": req.geo_alert,
        }).eq("item_id", item_id).execute()

        if not res.data:
            raise HTTPException(404, "Item not found or not authorised")

        bump_list_timestamp(req.list_id)
        return {"message": "Geo alert updated"}

    except Exception as e:
        print("[ERROR update_item_geo_alert]", e)
        raise HTTPException(500, "Failed to update geo alert")


@router.patch("/items/{item_id}/deadline")
def update_item_deadline(
    item_id: str,
    req: UpdateItemDeadlineRequest,
    token: str = Header(...),
):
    try:
        supabase.postgrest.auth(token)

        res = supabase.table("lists_items").update({
            "deadline": req.deadline,
        }).eq("item_id", item_id).execute()

        if not res.data:
            raise HTTPException(404, "Item not found or not authorised")

        bump_list_timestamp(req.list_id)
        return {"message": "Deadline updated"}

    except Exception as e:
        print("[ERROR update_item_deadline]", e)
        raise HTTPException(500, "Failed to update deadline")