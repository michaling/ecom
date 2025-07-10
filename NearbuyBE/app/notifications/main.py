import os
from datetime import datetime, timedelta, timezone
import uuid
from uuid import UUID
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Header, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from typing import Dict
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .deadline_checker import check_deadlines_and_notify
from sqlalchemy.dialects.postgresql import insert as pg_insert
from supabase_client import supabase


from .models import (
    Base,
    User,
    List,
    ListItem,
    ItemCategory,
    Store,
    StoreCategory,
    DeviceToken,
    UserStoreProximity,
    StoreItemAvailability,
    Alert,
    AlertsItems
)
from .utils import haversine_distance
from .expo_push import send_expo_push
from .database import get_db, engine
import requests

router = APIRouter()

# -------------------- 1. Load environment & set up DB --------------------

# Create tables if they don't exist (no-op if they already do)

Base.metadata.create_all(bind=engine)

#app = FastAPI(title="nearBuy (Expo + Notification)")
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""

# -------------------- Scheduler Setup --------------------


# -------------------- 3. Authentication Stub --------------------
# Replace with real JWT/Supabase Auth in production.

def verify_token_and_get_user_id(token: str) -> Optional[UUID]:
    """
    Stub: Validate the Bearer token, then return the user_id (UUID).
    For demo, we assume token == str(user_id).
    """
    try:
        return UUID(token)
    except:
        return None

async def get_current_user_id(
    authorization: str = Header(None)
) -> UUID:
    """
    Expects header: Authorization: Bearer <token>
    Returns the UUID of the logged-in user.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.split(" ")[1]
    user_id = verify_token_and_get_user_id(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id

# -------------------- 4. Pydantic Models for Requests --------------------

class RegisterExpoTokenRequest(BaseModel):
    user_id: UUID
    expo_push_token: str

class LocationUpdateRequest(BaseModel):
    user_id: UUID
    latitude: float
    longitude: float
    timestamp: datetime

# -------------------- 5. Helper: get all “geo_alert” item IDs for user --------------------

def get_user_geo_alert_item_ids(db: Session, user_id: UUID) -> list[int]:
    """
    Return a list of item IDs that appear in ANY of the user's lists,
    but only where list_items.geo_alert == True.
    """
    # Subquery: all list IDs for this user
    user_list_ids = db.query(List.list_id).filter(List.user_id == user_id).subquery()

    # Query distinct item_id from list_items where list_id in user's lists AND geo_alert=True
    items = (
        db.query(ListItem.item_id)
          .filter(
              ListItem.list_id.in_(user_list_ids),
              ListItem.geo_alert == True,
              ListItem.is_deleted == False
          )
          .distinct()
          .all()
    )
    return [row[0] for row in items]  # extract integers

# -------------------- 6. Helper: map those item IDs to category IDs --------------------

def get_category_ids_for_items(db: Session, item_ids: list[int]) -> list[int]:
    """
    Given a list of item IDs, return all distinct category IDs from items_categories.
    """
    if not item_ids:
        return []

    cats = (
        db.query(ItemCategory.category_id)
          .filter(ItemCategory.item_id.in_(item_ids))
          .distinct()
          .all()
    )
    return [row[0] for row in cats]

# -------------------- 7. Helper: find stores matching any of these categories --------------------

def get_stores_for_category_ids(db: Session, category_ids: list[int]) -> list[tuple]:
    """
    Given a list of category IDs, return tuples (store_id, store_name, latitude, longitude)
    for any store in stores_categories where store_category.category_id IN category_ids.
    """
    if not category_ids:
        return []

    stores = (
        db.query(Store.store_id, Store.name, Store.latitude, Store.longitude)
          .join(StoreCategory, Store.store_id == StoreCategory.store_id)
          .filter(StoreCategory.category_id.in_(category_ids))
          .distinct()
          .all()
    )
    return stores  # List of tuples: (id, name, lat, lon)

# -------------------- 8. Helper: fetch item names matching a store’s categories --------------------

def get_matching_item_names(db: Session, user_id: UUID, store_id: int) -> list[str]:
    """
    For a given user and store, return the item names (from the user's geo_alert items)
    that belong to any category of that store.
    """
    # A) Get user’s geo-alert item IDs
    user_item_ids = get_user_geo_alert_item_ids(db, user_id)
    if not user_item_ids:
        return []

    # B) Get the store’s category IDs
    store_category_rows = (
        db.query(StoreCategory.category_id)
          .filter(StoreCategory.store_id == store_id)
          .distinct()
          .all()
    )
    store_category_ids = [row[0] for row in store_category_rows]
    if not store_category_ids:
        return []

    # C) Find item IDs that are both in user_item_ids and in store_category_ids
    matching_item_id_rows = (
        db.query(ItemCategory.item_id)
          .filter(
              ItemCategory.item_id.in_(user_item_ids),
              ItemCategory.category_id.in_(store_category_ids)
          )
          .distinct()
          .all()
    )
    matching_item_ids = [row[0] for row in matching_item_id_rows]
    if not matching_item_ids:
        return []

    # D) Fetch the names of those matching items
    matching_item_name_rows = (
        db.query(ListItem.name)
          .filter(ListItem.item_id.in_(matching_item_ids))
          .all()
    )
    return [row[0] for row in matching_item_name_rows]  # e.g. ["Milk", "Eggs"]

# -------------------- 9. Endpoint: Register Expo Push Token --------------------

# @app.post("/register_expo_token")
# async def register_expo_token(
#     req: RegisterExpoTokenRequest,
#     current_user_id: UUID = Depends(get_current_user_id),
#     db: Session = Depends(get_db),
# ):
#     # 1) Ensure the body’s user_id matches the authenticated user
#     if req.user_id != current_user_id:
#         raise HTTPException(status_code=403, detail="Cannot register token for another user")
#
#     # 2) Create a new DeviceToken object (mapping to device_tokens table)
#     device = DeviceToken(
#         user_id=req.user_id,
#         expo_push_token=req.expo_push_token
#     )
#     db.add(device)
#     try:
#         db.commit()
#     except IntegrityError:
#         db.rollback()
#         # If token already exists for this user, ignore
#
#     return {"status": "ok", "detail": "Expo token registered"}

# -------------------- 10. Endpoint: Location Update --------------------

@router.post("/location_update")
def location_update(req: Dict, token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        user = supabase.auth.get_user()
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id

        db: Session = next(get_db())

        lat = req.get("latitude")
        lon = req.get("longitude")
        ts_str = req.get("timestamp")
        if not lat or not lon or not ts_str:
            raise HTTPException(400, "Missing lat/lon/timestamp")
        print("location: ", lat, ", ", lon)

        now_ts = datetime.now().replace(tzinfo=None)

        item_rows = (
            db.query(ListItem)
            .join(List, List.list_id == ListItem.list_id)
            .filter(
                List.user_id == user_id,
                ListItem.geo_alert == True,
                ListItem.is_deleted == False,
                ListItem.is_checked == False,
                (List.deadline.is_(None) | (List.deadline >= now_ts)),
                (ListItem.deadline.is_(None) | (ListItem.deadline >= now_ts))
            )
            .all()
        )
        if not item_rows:
            return {"status": "ok", "detail": "No geo_alert items", "alerts": []}

        store_rows = db.query(Store.store_id, Store.name, Store.latitude, Store.longitude).all()

        PROXIMITY_RADIUS = 500.0
        alerts = []

        for store_id, store_name, store_lat, store_lon in store_rows:
            dist = haversine_distance(lat, lon, store_lat, store_lon)

            if dist <= PROXIMITY_RADIUS:
                print(store_name, " is nearby")
                prox = db.query(UserStoreProximity).filter_by(user_id=user_id, store_id=store_id).first()
                if not prox:
                    prox = UserStoreProximity(user_id=user_id, store_id=store_id, entered_at=now_ts, notified=False)
                    db.add(prox)
                    db.commit()
                elif not prox.notified:
                    entered = prox.entered_at
                    if entered.tzinfo is not None:
                        entered = entered.astimezone(timezone.utc).replace(tzinfo=None)

                    available_names = []
                    if (now_ts.replace(tzinfo=None) - entered) >= timedelta(minutes=2):
                        for item in item_rows:
                            print(f" Checking availability for: {item.name}")
                            rec = db.query(StoreItemAvailability).filter_by(item_id=item.item_id, store_id=store_id).first()
                            if rec:
                                print("found availability record")
                                if rec.prediction:
                                    available_names.append(item.name)
                            else:
                                resp = requests.get("http://localhost:8000/check_product_availability", params={
                                    "product": item.name,
                                    "store": store_name
                                })
                                if resp.status_code != 200:
                                    print(f"Agent call failed: {resp.status_code} {resp.text}")
                                    continue
                                result = resp.json()
                                confidence = float(result.get("confidence", 0.0))
                                available_flag = bool(result.get("answer", False))
                                reason_text = result.get("reason")
                                new_rec = StoreItemAvailability(
                                    item_id=item.item_id,
                                    store_id=store_id,
                                    last_run=now_ts,
                                    prediction=available_flag,
                                    confidence=confidence,
                                    reason=reason_text
                                )
                                db.add(new_rec)
                                db.commit()
                                if available_flag:
                                    available_names.append(item.name)
                    print("available_names: ", available_names)
                    if available_names:
                        print(f"[DEBUG] MATCH! sending push for {store_name} with items: {available_names}")
                        alerts.append({
                            "store_id": str(store_id),
                            "store_name": store_name,
                            "items": available_names
                        })

                        now_utc = datetime.now()
                        batch = Alert(
                            user_id=user_id,
                            store_id=store_id,
                            alert_type="geo_alert",
                            last_triggered=now_utc
                        )
                        db.add(batch)
                        db.commit()
                        db.refresh(batch)

                        for item in item_rows:
                            if item.name in available_names:
                                stmt = pg_insert(AlertsItems).values(
                                    alert_id=batch.alert_id,
                                    item_id=item.item_id,
                                    list_id=item.list_id
                                ).on_conflict_do_nothing()
                                db.execute(stmt)
                        db.commit()

                        prox.notified = True
                        db.commit()
            else:
                prox = db.query(UserStoreProximity).filter_by(user_id=user_id, store_id=store_id).first()
                if prox:
                    db.delete(prox)
                    db.commit()

        return {"status": "ok", "detail": "Processed location update", "alerts": alerts}

    except Exception as e:
        print("[ERROR location_update]", e)
        raise HTTPException(status_code=500, detail="Failed to process location update")


# -------------------- 11. (Optional) Admin Endpoints --------------------

# Tester for the deadline alerts
@router.get("/admin/trigger_deadline_check")
async def manual_deadline_check(
    current_user_id: UUID = Depends(get_current_user_id),  # optional auth
):
    """
    Manually invoke the deadline checker (for testing). 
    In production, you might lock this down to admins only.
    """
    check_deadlines_and_notify()
    return {"status": "ok", "detail": "Deadline check triggered"}


@router.post("/run_deadline_check")
async def run_deadline_check(
    db: Session = Depends(get_db),
):
    # This will run your existing checker over all users/lists/items
    check_deadlines_and_notify()
    return {"status": "ok", "detail": "Deadlines processed"}
