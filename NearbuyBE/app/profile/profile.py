from fastapi import APIRouter, HTTPException, Header, Path
#from profile.models import
from supabase_client import supabase

router = APIRouter()

@router.get("/profile")
def get_profile(token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        user = supabase.auth.get_user()
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user.user.id

        res = (
            supabase.table("user_profiles")
            .select("geo_alert, display_name, is_admin")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not res.data:
            raise HTTPException(status_code=404, detail="Profile not found")

        return res.data

    except Exception as e:
        print("[ERROR get_profile]", e)
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

@router.patch("/profile/display_name")
def update_display_name(req: dict, token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        user = supabase.auth.get_user()
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user.user.id
        display_name = req.get("display_name")
        print("uid: ", user_id)
        print("new name: ", display_name)

        if not display_name:
            raise HTTPException(400, "Missing display_name")
        supabase.table("user_profiles").update({
            "display_name": display_name
        }).eq("user_id", user_id).execute()
        return {"message": "Display name updated"}

    except Exception as e:
        print("[ERROR update_display_name]", e)
        raise HTTPException(500, "Failed to update display name")

@router.patch("/profile/geo_alert")
def update_geo_alert(req: dict, token: str = Header(...)):
    try:
        supabase.postgrest.auth(token)
        user = supabase.auth.get_user()
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id
        geo_alert = req.get("geo_alert")

        if geo_alert is None:
            raise HTTPException(400, "Missing geo_alert")

        supabase.table("user_profiles").update({
            "geo_alert": geo_alert
        }).eq("user_id", user_id).execute()

        return {"message": "Geo alert updated"}

    except Exception as e:
        print("[ERROR update_geo_alert]", e)
        raise HTTPException(500, "Failed to update geo_alert")