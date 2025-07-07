from fastapi import APIRouter, Header, HTTPException
from supabase_client import supabase
from datetime import datetime
from collections import defaultdict
from .models import AlertCard, ListWithItems

router = APIRouter()

@router.get("/alerts_tab")
def get_alerts(
    token: str = Header(...),
):
    """
    Return ALL alerts for the logged-in user, newest first,
    already grouped exactly the way the app’s NotificationCard needs.
    """
    try:
        supabase.postgrest.auth(token)
        user = supabase.auth.get_user()
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id

        alerts = (
                supabase.table("alerts")
                .select("alert_id, store_id, alert_type, last_triggered")
                .eq("user_id", user_id)
                .order("last_triggered", desc=True)
                .execute()
                .data
                or []
        )
        if not alerts:
            return []

        alert_ids = [a["alert_id"] for a in alerts]
        store_ids = {a["store_id"] for a in alerts if a["store_id"]}

        links = (
                supabase.table("alerts_items")
                .select("alert_id, item_id")
                .in_("alert_id", alert_ids)
                .execute()
                .data
                or []
        )
        alert_to_items: Dict[str, List[str]] = defaultdict(list)
        item_ids: List[str] = []
        for row in links:
            alert_to_items[row["alert_id"]].append(row["item_id"])
            item_ids.append(row["item_id"])

        items = (
                supabase.table("lists_items")
                .select("item_id, name, list_id, deadline")
                .in_("item_id", item_ids or ["00000000-0000-0000-0000-000000000000"])
                .execute()
                .data
                or []
        )
        item_map = {it["item_id"]: it for it in items}
        list_ids = {it["list_id"] for it in items}

        list_name_map = {
            l["list_id"]: l["name"]
            for l in (
                    supabase.table("lists")
                    .select("list_id, name")
                    .in_("list_id", list_ids)
                    .execute()
                    .data
                    or []
            )
        }

        store_name_map = {}
        if store_ids:
            store_name_map = {
                s["store_id"]: s["name"]
                for s in (
                        supabase.table("stores")
                        .select("store_id, name")
                        .in_("store_id", list(store_ids))
                        .execute()
                        .data
                        or []
                )
            }

        result: List[AlertCard] = []
        for alert in alerts:
            grouped: Dict[str, List[str]] = defaultdict(list)
            deadlines: List[str] = []

            for iid in alert_to_items.get(alert["alert_id"], []):
                it = item_map.get(iid)
                if not it:
                    continue
                list_name = list_name_map.get(it["list_id"], "Unnamed List")
                grouped[list_name].append(it["name"])
                if it.get("deadline"):
                    deadlines.append(it["deadline"])

            # earliest deadline → "June 30"
            date_str = None
            if alert["alert_type"] == "deadline_alert" and deadlines:
                try:
                    dt = datetime.fromisoformat(min(deadlines))
                    date_str = dt.strftime("%B %-d")
                except Exception:
                    date_str = min(deadlines)[:10]

            result.append(
                AlertCard(
                    alert_id=alert["alert_id"],
                    type=alert["alert_type"],
                    timestamp=alert["last_triggered"],
                    storeName=store_name_map.get(alert["store_id"])
                    if alert["alert_type"] == "geo_alert"
                    else None,
                    date=date_str,
                    itemsByList=[
                        ListWithItems(listName=ln, items=its)
                        for ln, its in grouped.items()
                    ],
                )
            )
        # print(result)
        return result

    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR get_alerts]", e)
        raise HTTPException(500, "Failed to fetch alerts")