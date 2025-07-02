import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID

from .models import List, ListItem, DeviceToken, Alert, AlertsItems
from .expo_push import send_expo_push
from .database import get_db
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)

def check_deadlines_and_notify():
    db: Session = next(get_db())
    try:
        now = datetime.utcnow()
        window_end = now + timedelta(hours=24)

        list_alert_map: dict[UUID, UUID] = {}

        # --- 1) Notify lists approaching deadline ---
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
            body = f"Your list \"{lst.name}\" is due on {deadline_str} (within 24 h)."

            for (expo_token,) in tokens:
                send_expo_push(expo_token, title, body, {"list_name": lst.name})

            # create Alert record
            alert = Alert(
                user_id    = user_id,
                alert_type = "deadline_alert",
                last_triggered = now,
                list_id = lst.list_id
            )
            db.add(alert)
            db.commit()  # populate alert.alert_id

            list_alert_map[lst.list_id] = alert.alert_id

            # Mark list as notified
            lst.deadline_notified = True
            db.commit()


        # --- 2) Notify individual items approaching deadline ---
        due_items = (
            db.query(ListItem)
              .filter(
                  ListItem.deadline.isnot(None),
                  ListItem.deadline_notified == False,
                  ListItem.deadline >= now,
                  ListItem.deadline <= window_end,
                  ListItem.is_deleted == False
              )
              .all()
        )

        for item in due_items:
            # find the owning list to get user_id
            parent_list = (
                db.query(List)
                  .filter(List.list_id == item.list_id)
                  .one()
            )
            user_id: UUID = parent_list.user_id

            # insert to alerts_items if this item's deadline equals the list's deadline (list already notified)
            if item.deadline == parent_list.deadline:
                alert_id = list_alert_map.get(item.list_id)
                if alert_id:
                    stmt = pg_insert(AlertsItems).values(
                        alert_id = alert_id,
                        item_id  = item.item_id,
                        list_id  = item.list_id
                    ).on_conflict_do_nothing()
                    db.execute(stmt)

                    item.deadline_notified = True
                    db.commit()
                    
                continue

            tokens = db.query(DeviceToken.expo_push_token).filter(DeviceToken.user_id == user_id).all()

            title = "Item Deadline Approaching"
            deadline_str = item.deadline.strftime("%Y-%m-%d %H:%M UTC")
            body = f"Your item \"{item.name}\" is due on {deadline_str} (within 24 h)."

            for (expo_token,) in tokens:
                send_expo_push(expo_token, title, body, {"item_name": item.name})

            # create Alert record
            alert = Alert(
                user_id    = user_id,
                alert_type = "deadline_alert",
                last_triggered = now
            )
            db.add(alert)
            db.commit()  # populate alert.alert_id

            # link alert to this item in join table
            stmt = pg_insert(AlertsItems).values(
                alert_id = alert.alert_id,
                item_id  = item.item_id,
                list_id  = item.list_id
            ).on_conflict_do_nothing()
            db.execute(stmt)

            # mark item notified
            item.deadline_notified = True
            db.commit()

    except Exception as e:
        db.rollback()
        logger.error("Failed to commit deadline notifications: %s", e)
    #finally:
        #db.close()
