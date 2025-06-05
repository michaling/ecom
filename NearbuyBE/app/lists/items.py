from fastapi import APIRouter, HTTPException, Header
from app.supabase_client import supabase
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# --- Models ---
class RenameRequest(BaseModel):
    name: str

class CheckRequest(BaseModel):
    is_checked: bool

# --- Shared helper ---
def bump_list_timestamp_from_item(item_id: str):
    try:
        res = supabase.table("lists_items").select("list_id").eq("item_id", item_id).single().execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Item not found")
        list_id = res.data["list_id"]
        supabase.table("lists").update({
            "last_update": datetime.now().isoformat()
        }).eq("list_id", list_id).execute()
    except Exception as e:
        print("[ERROR bump_list_timestamp_from_item]", e)
        raise HTTPException(status_code=500, detail="Failed to update list timestamp")


# --- Rename item ---
@router.patch("/items/{item_id}/name")
def rename_item(item_id: str, req: RenameRequest):
    try:
        res = supabase.table("lists_items").update({
            "name": req.name
        }).eq("item_id", item_id).execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Item not found")

        bump_list_timestamp_from_item(item_id)
        return {"message": "Item renamed", "item_id": item_id}
    except Exception as e:
        print("[ERROR rename_item]", e)
        raise HTTPException(status_code=500, detail="Failed to rename item")


# --- Check or uncheck item ---
@router.patch("/items/{item_id}/check")
def check_item(
    item_id: str,
    req: CheckRequest,
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

        bump_list_timestamp_from_item(item_id)
        return {"message": "Item checked/unchecked", "item_id": item_id}

    except Exception as e:
        print("[ERROR check_item]", e)
        raise HTTPException(status_code=500, detail="Failed to update check status")


# --- Soft delete ---
@router.delete("/items/{item_id}")
def delete_item(item_id: str):
    try:
        now = datetime.utcnow().isoformat()
        res = supabase.table("lists_items").update({
            "is_deleted": True,
            "deleted_at": now
        }).eq("item_id", item_id).execute()

        if not res.data:
            raise HTTPException(status_code=404, detail="Item not found")

        bump_list_timestamp_from_item(item_id)
        return {"message": "Item deleted", "item_id": item_id}
    except Exception as e:
        print("[ERROR delete_item]", e)
        raise HTTPException(status_code=500, detail="Failed to delete item")