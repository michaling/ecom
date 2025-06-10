import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID

from models import List, ListItem, DeviceToken
from expo_push import send_expo_push
from utils import get_db

logger = logging.getLogger(__name__)

def check_deadlines_and_notify():
    """
    1) Notify any List with a deadline within the next 24 hours, if deadline_notified == False.
    2) Notify any ListItem with its own deadline within the next 24 hours, if:
         - ListItem.deadline_notified == False
         - ListItem.deadline != parent List.deadline
       (i.e. skip items that share exactly the List’s deadline, because the list notification already covers them.)
    After sending a push, set the respective deadline_notified = True and commit once at the end.
    """
    db: Session = next(get_db())
    now = datetime.utcnow()
    window_end = now + timedelta(hours=24)

    # --- 1) Find and notify lists ---
    due_lists = (
        db.query(List)
          .filter(
              List.deadline.isnot(None),
              List.deadline_notified == False,
              List.deadline >= now,
              List.deadline <= window_end,
              List.is_deleted == False
          )
          .all()
    )

    for lst in due_lists:
        user_id: UUID = lst.user_id
        tokens = db.query(DeviceToken.expo_push_token).filter(DeviceToken.user_id == user_id).all()

        title = "List Deadline Approaching"
        deadline_str = lst.deadline.strftime("%Y-%m-%d %H:%M UTC")
        body = f"Your list “{lst.name}” is due on {deadline_str} (within 24 h)."

        for (expo_token,) in tokens:
            send_expo_push(expo_token, title, body, {"list_name": str(lst.name)})

        lst.deadline_notified = True

    # --- 2) Find and notify items with their own deadlines, but skip if date == parent list’s ---
    due_items = (
        db.query(ListItem)
          .join(List, ListItem.list_id == List.id)
          .filter(
              ListItem.deadline.isnot(None),
              ListItem.deadline_notified == False,
              ListItem.deadline >= now,
              ListItem.deadline <= window_end,
              ListItem.deadline != List.deadline,
              List.is_deleted == False,
              ListItem.is_deleted == False
          )
          .all()
    )

    for item in due_items:
        user_id: UUID = item.user_id
        tokens = db.query(DeviceToken.expo_push_token).filter(DeviceToken.user_id == user_id).all()

        title = "Item Deadline Approaching"
        deadline_str = item.deadline.strftime("%Y-%m-%d %H:%M UTC")
        body = f"Your item “{item.item_name}” is due on {deadline_str} (within 24 h)."

        for (expo_token,) in tokens:
            send_expo_push(expo_token, title, body, {"item_name": str(item.name)})

        item.deadline_notified = True

    # --- 3) Commit all changes in one transaction ---
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to commit deadline notifications: %s", e)
    finally:
        db.close()
