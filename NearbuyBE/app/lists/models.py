from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# List models:
class ListItem(BaseModel):
    name: str
    is_checked: bool = False
    deadline: Optional[datetime] = None
    geo_alert: Optional[bool] = None


class PartialListItem(BaseModel):
    name: Optional[str] = None
    is_checked: Optional[bool] = None
    deadline: Optional[datetime] = None
    geo_alert: Optional[bool] = None


class UserList(BaseModel):
    name: str
    deadline: Optional[datetime] = None
    geo_alert: Optional[bool] = None
    pic_path: Optional[str] = None


class CreateItemRequest(BaseModel):
    item_name: str
    geo_alert: bool | None = None
    deadline: str | None = None


# Items Models:
class RenameItemRequest(BaseModel):
    name: str
    list_id: str


class CheckItemRequest(BaseModel):
    is_checked: bool
    list_id: str


class DeleteItemRequest(BaseModel):
    list_id: str


class UpdateItemGeoAlertRequest(BaseModel):
    list_id: str
    geo_alert: bool


class UpdateItemDeadlineRequest(BaseModel):
    list_id: str
    deadline: str | None
