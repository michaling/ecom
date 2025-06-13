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