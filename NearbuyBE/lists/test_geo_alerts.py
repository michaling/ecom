# ──────────────────────────────────────────────────────────
# test_geo_alerts.py
# ──────────────────────────────────────────────────────────
from fastapi.testclient import TestClient
from lists import app
from test_lists import set_global_geo, iso_after   # ↩︎ use your existing helpers

client  = TestClient(app)
user_id = "18293cd2-18b4-4b88-9f92-85ae3e50dc68"


# small helper to fetch a single list (remote DB state)
def fetch_list(lid: str):
    resp = client.get(f"/lists/{lid}")
    assert resp.status_code == 200
    return resp.json()


# ───────────────── 1. list can turn TRUE → FALSE ─────────
def test_list_override_to_false():
    set_global_geo(True)                                # profile default TRUE

    create = client.post(
        "/lists/",
        params={"user_id": user_id},
        json={
            "id": None,
            "name": "geo off at list",
            "deadline": None,
            "geo_alert": False,                         # override here
            "items": [
                {"name": "A", "is_checked": False}
            ]
        },
    )
    lid = create.json()["list_id"]

    data = fetch_list(lid)
    assert data["geo_alert"] is False
    assert all(item["geo_alert"] is False for item in data["items"])


# ──────────────── 2. item can turn TRUE → FALSE ──────────
def test_item_override_to_false():
    set_global_geo(True)                                # default TRUE again

    create = client.post(
        "/lists/",
        params={"user_id": user_id},
        json={
            "id": None,
            "name": "item geo off",
            "deadline": None,
            # list inherits default (TRUE) because we omit the field
            "items": [
                {"name": "should alert",  "is_checked": False},  # inherits TRUE
                {"name": "no alert",      "is_checked": False, "geo_alert": False},
            ],
        },
    )
    lid  = create.json()["list_id"]
    data = fetch_list(lid)

    assert data["geo_alert"] is True
    assert data["items"][0]["geo_alert"] is True
    assert data["items"][1]["geo_alert"] is False          # overridden


# ───────── list FALSE but one item bumps back to TRUE ────
def test_item_override_true_when_list_false():
    set_global_geo(True)

    create = client.post(
        "/lists/",
        params={"user_id": user_id},
        json={
            "id": None,
            "name": "mixed",
            "deadline": None,
            "geo_alert": False,                    # list turns it off
            "items": [
                {"name": "wake me!", "is_checked": False, "geo_alert": True},
                {"name": "still off", "is_checked": False},
            ],
        },
    )
    lid  = create.json()["list_id"]
    data = fetch_list(lid)

    assert data["geo_alert"] is False
    assert data["items"][0]["geo_alert"] is True
    assert data["items"][1]["geo_alert"] is False


# ───────── profile FALSE but list turns TRUE for all ─────
def test_profile_false_list_true():
    set_global_geo(False)                               # default now FALSE

    create = client.post(
        "/lists/",
        params={"user_id": user_id},
        json={
            "id": None,
            "name": "turn on alerts",
            "deadline": iso_after(3),
            "geo_alert": True,                          # list override → TRUE
            "items": [
                {"name": "X", "is_checked": False},     # inherits TRUE
                {"name": "Y", "is_checked": False},
            ],
        },
    )
    lid  = create.json()["list_id"]
    data = fetch_list(lid)

    assert data["geo_alert"] is True
    assert all(item["geo_alert"] is True for item in data["items"])
