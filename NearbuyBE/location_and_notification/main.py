# backend/main.py

import os
from datetime import datetime, timedelta
from uuid import UUID
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from dotenv import load_dotenv

from models import (
    Base,
    User,
    List,
    ListItem,
    ItemCategory,
    Store,
    StoreCategory,
    DeviceToken,
    UserStoreProximity
)
from utils import haversine_distance
from expo_push import send_expo_push

# -------------------- 1. Load environment & set up DB --------------------

load_dotenv()  # loads .env file

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist (no-op if they already do)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="nearBuy (Expo + Category Detailed Notification)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- 2. Dependency: DB Session --------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

def get_user_geo_alert_item_ids(db: Session, user_id: UUID) -> List[int]:
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
              ListItem.geo_alert == True
          )
          .distinct()
          .all()
    )
    return [row[0] for row in items]  # extract integers

# -------------------- 6. Helper: map those item IDs to category IDs --------------------

def get_category_ids_for_items(db: Session, item_ids: List[int]) -> List[int]:
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

def get_stores_for_category_ids(db: Session, category_ids: List[int]) -> List[tuple]:
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

def get_matching_item_names(db: Session, user_id: UUID, store_id: int) -> List[str]:
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

@app.post("/register_expo_token")
async def register_expo_token(
    req: RegisterExpoTokenRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # 1) Ensure the body’s user_id matches the authenticated user
    if req.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot register token for another user")

    # 2) Create a new DeviceToken object (mapping to device_tokens table)
    device = DeviceToken(
        user_id=req.user_id,
        expo_push_token=req.expo_push_token
    )
    db.add(device)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # If token already exists for this user, ignore

    return {"status": "ok", "detail": "Expo token registered"}

# -------------------- 10. Endpoint: Location Update --------------------

@app.post("/location_update")
async def location_update(
    req: LocationUpdateRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # 1) Verify that the request’s user_id matches the authenticated user
    if req.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Cannot send location for another user")

    user_id = req.user_id
    user_lat = req.latitude
    user_lon = req.longitude
    now_ts: datetime = req.timestamp

    # 2) Get all item IDs from this user’s lists where geo_alert == True
    user_item_ids = get_user_geo_alert_item_ids(db, user_id)
    if not user_item_ids:
        return {"status": "ok", "detail": "No geo_alert items on any list"}

    # 3) Map those item IDs → category IDs via items_categories
    user_category_ids = get_category_ids_for_items(db, user_item_ids)
    if not user_category_ids:
        return {"status": "ok", "detail": "No categories found for geo_alert items"}

    # 4) Find all stores matching any of these categories via stores_categories
    store_rows = get_stores_for_category_ids(db, user_category_ids)
    # store_rows: list of tuples (store_id, store_name, store_lat, store_lon)

    # 5) For each store, compute distance and handle geofence + dwell logic
    PROXIMITY_RADIUS = 500.0  # meters

    for store_id, store_name, store_lat, store_lon in store_rows:
        dist = haversine_distance(user_lat, user_lon, store_lat, store_lon)

        if dist <= PROXIMITY_RADIUS:
            # User is within radius: check or insert proximity row
            prox: Optional[UserStoreProximity] = (
                db.query(UserStoreProximity)
                  .filter_by(user_id=user_id, store_id=store_id)
                  .first()
            )
            if not prox:
                # No proximity row exists: insert with entered_at = now, notified=False
                new_row = UserStoreProximity(
                    user_id=user_id,
                    store_id=store_id,
                    entered_at=now_ts,
                    notified=False
                )
                db.add(new_row)
                db.commit()
            else:
                # Proximity row exists; check dwell time and notification
                if not prox.notified:
                    elapsed = now_ts - prox.entered_at
                    if elapsed >= timedelta(minutes=5):
                        # ≥5 minutes: send detailed push
                        item_names = get_matching_item_names(db, user_id, store_id)

                        if item_names:
                            # Show up to 5 items, then “…and N more” if necessary
                            MAX_SHOW = 5
                            if len(item_names) > MAX_SHOW:
                                shown = item_names[:MAX_SHOW]
                                remaining = len(item_names) - MAX_SHOW
                                bullet_list = "\n".join(f"• {n}" for n in shown)
                                body = (
                                    f"You've been near {store_name} for 5 minutes.\n"
                                    f"They carry these items from your list:\n{bullet_list}\n"
                                    f"…and {remaining} more items."
                                )
                            else:
                                bullet_list = "\n".join(f"• {n}" for n in item_names)
                                body = (
                                    f"You've been near {store_name} for 5 minutes.\n"
                                    f"They carry these items from your list:\n{bullet_list}"
                                )
                        else:
                            # Fallback (unlikely if store_rows was filtered correctly)
                            body = f"You've been near {store_name} for 5 minutes. They carry items on your list!"

                        tokens = (
                            db.query(DeviceToken.expo_push_token)
                              .filter(DeviceToken.user_id == user_id)
                              .all()
                        )
                        for (expo_token,) in tokens:
                            title = f"Store Nearby: {store_name}"
                            data_payload = {
                                "store_id": store_id,
                                "store_name": store_name,
                                "item_names": item_names  # optional deep-link data
                            }
                            send_expo_push(expo_token, title, body, data_payload)

                        # Mark as notified to avoid duplicate pushes
                        prox.notified = True
                        db.commit()
        else:
            # Outside radius: if a proximity row exists, delete it (reset timer)
            prox: Optional[UserStoreProximity] = (
                db.query(UserStoreProximity)
                  .filter_by(user_id=user_id, store_id=store_id)
                  .first()
            )
            if prox:
                db.delete(prox)
                db.commit()

    return {"status": "ok", "detail": "Processed location update"}

# -------------------- 11. (Optional) Admin Endpoints --------------------
# To run locally: uvicorn main:app --reload --host 0.0.0.0 --port 8000
