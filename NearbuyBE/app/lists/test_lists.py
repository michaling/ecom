# tests/test_lists_geo.py
"""
Comprehensive geo_alert test-suite
• profile default TRUE/FALSE
• list-level override
• item-level override
• inheritance
• update list
• delete & restore
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from lists import app
from supabase_client import supabase

client = TestClient(app)
user_id = "18293cd2-18b4-4b88-9f92-85ae3e50dc68"


# ───────────────────────── helpers ──────────────────────────
def iso_after(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).isoformat() + "Z"


def set_global_geo(flag: bool) -> None:
    """Flip geo_alert in user_profiles for the test user."""
    tbl = supabase.table("user_profiles")
    if tbl.select("user_id").eq("user_id", user_id).execute().data:
        tbl.update({"geo_alert": flag}).eq("user_id", user_id).execute()
    else:  # first time → insert stub record
        tbl.insert(
            {
                "user_id": user_id,
                "display_name": "pytest",
                "geo_alert": flag,
                "email_verified": False,
            }
        ).execute()


# MODIFIED: new_list now returns a tuple (list_dict, list_id)
def new_list(payload: dict) -> tuple[dict, str]:
    """POST /lists/ and GET it back as dict, also returning the list_id."""
    res = client.post("/lists/", params={"user_id": user_id}, json=payload)
    res.raise_for_status()
    list_id = res.json()["list_id"] # This correctly gets list_id from the POST response
    return client.get(f"/lists/{list_id}").json(), list_id # Return the GET result and the list_id


# ───────────────────────── test cases ───────────────────────
def test_profile_true_default_inheritance():
    """
    Profile TRUE, no overrides → list & items TRUE
    """
    set_global_geo(True)

    # MODIFIED: Unpack the tuple here
    lst, _ = new_list(
        {
            "id": None,
            "name": "defaults",
            "deadline": None,
            # geo_alert omitted
            "items": [
                {"name": "A", "is_checked": False},
                {"name": "B", "is_checked": False},
            ],
        }
    )
    assert lst["geo_alert"] is True
    for it in lst["items"]:
        assert it["geo_alert"] is True


def test_profile_true_list_false_and_mixed_items():
    """
    Profile TRUE, list says False → items inherit False
    but an item can flip back to True.
    """
    set_global_geo(True)

    # MODIFIED: Unpack the tuple here
    lst, _ = new_list(
        {
            "id": None,
            "name": "list false",
            "geo_alert": False,
            "deadline": None,
            "items": [
                {"name": "off-child"},  # inherits False
                {"name": "on-child", "geo_alert": True},
            ],
        }
    )
    assert lst["geo_alert"] is False
    assert lst["items"][0]["geo_alert"] is False
    assert lst["items"][1]["geo_alert"] is True


def test_profile_false_list_true_and_item_false():
    """
    Profile FALSE, list flips to True → items inherit True
    but one item can turn it off again.
    """
    set_global_geo(False)

    # MODIFIED: Unpack the tuple here
    lst, _ = new_list(
        {
            "id": None,
            "name": "list true",
            "geo_alert": True,
            "deadline": None,
            "items": [
                {"name": "inherit-on"},  # inherits True
                {"name": "override-off", "geo_alert": False},
            ],
        }
    )
    assert lst["geo_alert"] is True
    assert lst["items"][0]["geo_alert"] is True
    assert lst["items"][1]["geo_alert"] is False


def test_update_preserves_and_applies_inheritance():
    """
    Updating a list re-evaluates inheritance for *new* items
    but leaves untouched ones as provided.
    """
    set_global_geo(True)

    # create first
    # MODIFIED: Unpack the tuple here
    original_list_data, list_id = new_list(
        {
            "id": None,
            "name": "to-update",
            "deadline": None,
            "geo_alert": False,  # list FALSE
            "items": [
                {"name": "stay-false"},  # will keep False
            ],
        }
    )
    # The list_id is now correctly obtained from the new_list return
    # list_id = original["list_id"] # This line is no longer needed/problematic

    # update – add one more item (no explicit field) & bump list to True
    upd = client.put(
        f"/lists/{list_id}",
        json={
            "id": list_id,
            "name": "updated",
            "deadline": None,
            "geo_alert": True,
            "items": [
                {"name": "stay-false", "is_checked": False, "geo_alert": False},
                {"name": "new-inherits"},
            ],
        },
    )
    assert upd.status_code == 200

    lst = client.get(f"/lists/{list_id}").json()
    assert lst["geo_alert"] is True
    assert lst["items"][0]["geo_alert"] is False          # explicit
    assert lst["items"][1]["geo_alert"] is True           # inherited


def test_delete_and_restore_keeps_geo_flags():
    """
    Soft-delete then restore must not change any geo_alert flags.
    """
    set_global_geo(False)

    # create list with mix
    create = client.post(
        "/lists/",
        params={"user_id": user_id},
        json={
            "id": None,
            "name": "trash-me",
            "geo_alert": True,
            "deadline": None,
            "items": [
                {"name": "A", "geo_alert": False},
                {"name": "B"},
            ],
        },
    )
    list_id = create.json()["list_id"] # This was already directly from the POST response, so it's fine.

    # delete
    client.delete(f"/lists/{list_id}").raise_for_status()
    # restore
    client.post(f"/lists/{list_id}/restore").raise_for_status()

    lst = client.get(f"/lists/{list_id}").json()
    assert lst["geo_alert"] is True
    assert lst["items"][0]["geo_alert"] is False
    assert lst["items"][1]["geo_alert"] is True