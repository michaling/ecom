from fastapi.testclient import TestClient
from lists import app
from supabase_client import supabase
from datetime import datetime, timedelta

client  = TestClient(app)
user_id = "18293cd2-18b4-4b88-9f92-85ae3e50dc68"   # your test user

# ---------- helpers ---------------------------------------------------------------- #
TABLE = "user_profiles"        # change only if your table is named differently
DUMMY_NAME = "pytest-bot"      # satisfies NOT-NULL display_name

def set_global_geo(flag: bool):
    """
    Upsert a row in user_profiles with the required NOT-NULL columns.
    """
    row = {"user_id": user_id,
           "display_name": DUMMY_NAME,
           "geo_alert": flag}

    # first try update; if count==0 insert
    if not supabase.table(TABLE).update(
            {"geo_alert": flag}).eq("user_id", user_id).execute().data:
        supabase.table(TABLE).insert(row).execute()

def iso_after(days: int):
    return (datetime.utcnow() + timedelta(days=days)).isoformat()

# ----------------------------------------------------------------------------------- #
def test_create_list_basic():
    set_global_geo(False)

    resp = client.post("/lists/", params={"user_id": user_id}, json={
        "id": None,
        "name": "Test Grocery List",
        "deadline": None,
        "geo_alert": False,
        "items": [
            {"name": "Milk",  "is_checked": False, "deadline": None, "geo_alert": False},
            {"name": "Eggs",  "is_checked": True,  "deadline": None, "geo_alert": True}
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "list_id" in data and data["message"] == "List created"

# ----------------------------------------------------------------------------------- #
def test_get_user_lists_with_geo_false():
    set_global_geo(False)
    resp = client.get("/lists/", params={"user_id": user_id})
    assert resp.status_code == 200
    arr = resp.json()
    if arr:
        assert "geo_alert" in arr[0]

# ----------------------------------------------------------------------------------- #
def test_update_deadline_and_items():
    set_global_geo(False)

    # ---------- first POST ----------
    first_deadline = iso_after(1)                 # already str
    create = client.post("/lists/", params={"user_id": user_id}, json={
        "id": None,
        "name": "Deadline Demo",
        "deadline": first_deadline,
        "geo_alert": False,
        "items": [
            {
                "name": "Water",
                "is_checked": False,
                "deadline": None,
                "geo_alert": False
            }
        ]
    })
    list_id = create.json()["list_id"]

    # ---------- update PUT ----------
    new_dead = iso_after(7)                       # str
    upd = client.put(f"/lists/{list_id}", json={
        "id": list_id,
        "name": "Deadline Demo Updated",
        "deadline": new_dead,
        "geo_alert": False,
        "items": [
            {
                "name": "Bananas",
                "is_checked": True,
                "deadline": new_dead,
                "geo_alert": False
            }
        ]
    })
    assert upd.status_code == 200


# ----------------------------------------------------------------------------------- #
def test_delete_and_restore():
    set_global_geo(False)
    create = client.post("/lists/", params={"user_id": user_id}, json={
        "id": None,
        "name": "Trash Me",
        "deadline": None,
        "geo_alert": False,
        "items": [{"name": "X", "is_checked": False, "deadline": None, "geo_alert": False}]
    })
    list_id = create.json()["list_id"]
    client.delete(f"/lists/{list_id}")
    res = client.post(f"/lists/{list_id}/restore")
    assert res.status_code == 200

# ----------------------------------------------------------------------------------- #
def test_global_geo_alert_forces_true():
    set_global_geo(True)             # flip the global switch ON

    create = client.post("/lists/", params={"user_id": user_id}, json={
        "id": None,
        "name": "Forced GEO",
        "deadline": None,
        "geo_alert": False,         # user tries to send False
        "items": [
            {"name": "Loc1", "is_checked": False, "deadline": None, "geo_alert": False},
            {"name": "Loc2", "is_checked": False, "deadline": None}  # omitted field
        ]
    })
    list_id = create.json()["list_id"]
    lst = client.get(f"/lists/{list_id}").json()
    assert lst["geo_alert"] is True
    for itm in lst["items"]:
        assert itm["geo_alert"] is True

    set_global_geo(False)            # reset for other devs
