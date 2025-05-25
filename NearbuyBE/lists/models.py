from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ListItem(BaseModel):
    name: str
    is_checked: bool = False
    deadline: Optional[datetime] = None
    geo_alert: bool = False

class UserList(BaseModel):
    id: Optional[str]
    name: str
    items: List[ListItem]
    shared: bool = False
    deadline: Optional[datetime] = None
    geo_alert: bool = False
