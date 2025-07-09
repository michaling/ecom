from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "user_profiles"
    user_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    #email = Column(String, unique=True, nullable=False)
    # (password_hash, created_at, etc.)

class List(Base):
    __tablename__ = "lists"
    list_id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    deadline = Column(DateTime(timezone=False), nullable=True)  
    deadline_notified = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    # (deadline, etc.)

class ListItem(Base):
    """
    We add a `geo_alert` column here. Only if geo_alert=True will this
    item be considered when doing proximity checks.
    """
    __tablename__ = "lists_items"
    item_id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)
    list_id = Column(PGUUID(as_uuid=True), ForeignKey("lists.list_id", ondelete="CASCADE"), nullable=False)
    geo_alert = Column(Boolean, default=False, nullable=False)
    name = Column(String, nullable=False)
    deadline = Column(DateTime(timezone=False), nullable=True)  
    deadline_notified = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    is_checked = Column(Boolean, nullable=False, default=False)

"""
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    # (category, description, etc.)
"""

class Store(Base):
    __tablename__ = "stores"
    store_id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

class ItemCategory(Base):
    """
    Maps items → categories. 
    Corresponds to your Supabase table 'items_categories'.
    """
    __tablename__ = "items_categories"
    item_id = Column(PGUUID(as_uuid=True), ForeignKey("lists_items.item_id", ondelete="CASCADE"), primary_key=True, index=True)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="CASCADE"), nullable=False)

class StoreCategory(Base):
    """
    Maps stores → categories.
    Corresponds to your Supabase table 'stores_categories'.
    """
    __tablename__ = "stores_categories"
    store_id = Column(PGUUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), primary_key=True, index=True)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="CASCADE"), nullable=False)

class Categories(Base):
    __tablename__ = "categories"
    category_id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)

class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False)
    expo_push_token = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "expo_push_token", name="uniq_user_expo_token"),)

class UserStoreProximity(Base):
    __tablename__ = "user_store_proximity"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    entered_at = Column(DateTime(timezone=True), nullable=False)
    notified = Column(Boolean, default=False, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "store_id", name="uniq_user_store"),)

class StoreItemAvailability(Base):
    __tablename__ = "store_item_availability"
    item_id    = Column(PGUUID(as_uuid=True), ForeignKey("lists_items.item_id", ondelete="CASCADE"), primary_key=True)
    store_id   = Column(PGUUID(as_uuid=True), ForeignKey("stores.store_id",  ondelete="CASCADE"), primary_key=True)
    last_run   = Column(DateTime(timezone=True), nullable=False)
    prediction = Column(Boolean, nullable=False)
    confidence = Column(Float,   nullable=False)
    reason = Column(String, nullable=True)

class Alert(Base):
    __tablename__   = "alerts"
    alert_id        = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    user_id         = Column(PGUUID(as_uuid=True), ForeignKey("user_profiles.user_id", ondelete="CASCADE"), nullable=False)
    store_id        = Column(PGUUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=True)
    alert_type      = Column(String, nullable=False)
    last_triggered = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    list_id         = Column(PGUUID(as_uuid=True), ForeignKey("lists.list_id", ondelete="CASCADE"), nullable=True)

class AlertsItems(Base):
    __tablename__   = "alerts_items"
    alert_id        = Column(PGUUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    item_id         = Column(PGUUID(as_uuid=True), ForeignKey("lists_items.item_id", ondelete="CASCADE"), primary_key=True)
    list_id         = Column(PGUUID(as_uuid=True), ForeignKey("lists.list_id", ondelete="CASCADE"), nullable=False)
