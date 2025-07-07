from fastapi import APIRouter, HTTPException, Header
from supabase_client import supabase

router = APIRouter()

@router.post("/device_token")
def save_device_token(req: dict, token: str = Header(...)):
    """
    Store (or update) the Expo push token for the logged-in user.
    The request body must contain:
        {
          "expo_push_token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"
        }
    """
    try:
        # Authenticate the Supabase client with the user’s JWT
        supabase.postgrest.auth(token)
        user = supabase.auth.get_user()
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user.user.id
        expo_push_token = req.get("expo_push_token")

        if not expo_push_token:
            raise HTTPException(status_code=400, detail="Missing expo_push_token")

        # Insert into device_tokens
        supabase.table("device_tokens").upsert({
            "user_id": user_id,
            "expo_push_token": expo_push_token,
        },
            on_conflict="user_id,expo_push_token",
            ignore_duplicates=True
        ).execute()

        return {"message": "Push token stored"}

    except Exception as e:
        print("[ERROR save_device_token]", e)
        raise HTTPException(status_code=500, detail="Failed to save push token")