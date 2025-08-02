from datetime import datetime, timedelta
import supabase
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.delete("/cleanup")
def cleanup_old_deleted():
    threshold = (datetime.now() - timedelta(days=30)).isoformat()

    # 1. Delete old deleted items
    old_items = (
        supabase.table("lists_items")
        .delete()
        .eq("is_deleted", True)
        .lte("deleted_at", threshold)
        .execute()
    )

    # 2. Delete old deleted lists
    old_lists = (
        supabase.table("lists")
        .delete()
        .eq("is_deleted", True)
        .lte("deleted_at", threshold)
        .execute()
    )

    return {
        "items_deleted": old_items.data if old_items.data else 0,
        "lists_deleted": old_lists.data if old_lists.data else 0,
    }
