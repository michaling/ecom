# tests/test_notifications.py

import sys
import os
from datetime import datetime, timedelta
import uuid
import pytest

#TODO
# ensure project root is on PYTHONPATH so imports resolve
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "app"))  # allow imports from app/

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# import modules for testing
import notifications.database as database
import notifications.deadline_checker as deadline_checker
from notifications.main import app
from notifications.models import (
    Base,
    User,
    List,
    ListItem,
    Categories as Category,
    ItemCategory,
    Store,
    StoreCategory,
    DeviceToken,
    StoreItemAvailability,
    Alert,
    AlertsItems,
)
from notifications.deadline_checker import check_deadlines_and_notify
from notifications.database import get_db, SessionLocal

# ----- Fixtures -----


@pytest.fixture(scope="session")
def engine():
    return create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )


@pytest.fixture(scope="session")
def tables(engine):
    # create all tables based on notifications.models.Base
    Base.metadata.create_all(bind=engine)
    yield
    # drop all tables after tests complete
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def override_get_db(monkeypatch, db_session):
    # override the dependency in database and deadline_checker
    def _get_db():
        try:
            yield db_session
        finally:
            pass

    monkeypatch.setattr(database, "get_db", _get_db)
    monkeypatch.setattr(deadline_checker, "get_db", _get_db)


@pytest.fixture
def client(db_session):
    # override FastAPI dependency to use our session
    def override_dep():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_dep
    return TestClient(app)


# ----- Seed helpers -----


def seed_geo_alert_scenario(db):
    user = User(user_id=uuid.uuid4())
    db.add(user)

    lst = List(list_id=uuid.uuid4(), user_id=user.user_id, name="Groceries")
    db.add(lst)

    item = ListItem(
        item_id=uuid.uuid4(), list_id=lst.list_id, name="Milk", geo_alert=True
    )
    db.add(item)

    cat = Category(category_id=uuid.uuid4())
    db.add(cat)
    db.flush()
    db.add(ItemCategory(item_id=item.item_id, category_id=cat.category_id))

    store = Store(
        store_id=uuid.uuid4(), name="CornerStore", latitude=32.0, longitude=34.8
    )
    db.add(store)
    db.flush()
    db.add(StoreCategory(store_id=store.store_id, category_id=cat.category_id))

    db.add(DeviceToken(user_id=user.user_id, expo_push_token="dummy-token"))

    db.add(
        StoreItemAvailability(
            store_id=store.store_id,
            last_run=datetime.now(),
            prediction=True,
            confidence=0.9,
            reason="in stock",
            item_name=item.name,
        )
    )

    db.commit()
    return user, item, store


def seed_deadline_scenario(db):
    user = User(user_id=uuid.uuid4())
    db.add(user)

    due = datetime.now() + timedelta(hours=12)
    lst = List(
        list_id=uuid.uuid4(),
        user_id=user.user_id,
        name="To Do",
        deadline=due,
        deadline_notified=False,
    )
    db.add(lst)

    item = ListItem(
        item_id=uuid.uuid4(),
        list_id=lst.list_id,
        name="Finish report",
        deadline=due - timedelta(hours=1),
        deadline_notified=False,
    )
    db.add(item)

    db.add(DeviceToken(user_id=user.user_id, expo_push_token="dummy-token"))

    db.commit()
    return user, lst, item


# ----- Tests -----


def test_geo_alert_inserts_alerts_and_link_rows(db_session, client):
    user, item, store = seed_geo_alert_scenario(db_session)

    payload = {
        "user_id": str(user.user_id),
        "latitude": store.latitude,
        "longitude": store.longitude,
        "timestamp": datetime.now().isoformat(),
    }
    resp = client.post(
        "/location_update",
        json=payload,
        headers={"Authorization": f"Bearer {user.user_id}"},
    )
    assert resp.status_code == 200

    alerts = db_session.query(Alert).filter_by(user_id=user.user_id).all()
    assert len(alerts) == 1
    alert = alerts[0]

    links = (
        db_session.query(AlertsItems)
        .filter_by(alert_id=alert.alert_id, item_id=item.item_id)
        .all()
    )
    assert len(links) == 1


def test_deadline_checker_inserts_list_and_item_alerts(db_session):
    user, lst, item = seed_deadline_scenario(db_session)

    check_deadlines_and_notify()

    alerts = db_session.query(Alert).filter_by(user_id=user.user_id).all()
    assert len(alerts) == 2

    item_links = db_session.query(AlertsItems).filter_by(item_id=item.item_id).all()
    assert len(item_links) == 1

    updated_list = db_session.query(List).get(lst.list_id)
    assert updated_list.deadline_notified

    updated_item = db_session.query(ListItem).get(item.item_id)
    assert updated_item.deadline_notified
