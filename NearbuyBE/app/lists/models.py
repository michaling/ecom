from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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