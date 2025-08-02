from pydantic import BaseModel
from typing import List, Optional


class ListWithItems(BaseModel):
    listId: str
    listName: str
    items: List[str]


class AlertCard(BaseModel):
    """
    Shape that the mobile NotificationCard expects.
    """

    alert_id: str
    type: str  # "geo_alert" or "deadline_alert"
    timestamp: str
    storeName: Optional[str]  # only relevant for geo_alert
    date: Optional[str]  # only relevant for deadline_alert
    itemsByList: List[ListWithItems]
