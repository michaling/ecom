from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ListItem(BaseModel):
    name: str
    is_checked: bool = False
    deadline: Optional[datetime] = None
    geo_alert: Optional[bool] = None

class UserList(BaseModel):
    id: Optional[str]
    name: str
    items: List[ListItem]
    deadline: Optional[datetime] = None
    geo_alert: Optional[bool] = None
