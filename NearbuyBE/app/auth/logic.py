from app.supabase_client import supabase

def _extract_msg(err: Exception) -> str:
    return str(err)

def sign_in(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        return res.user
    except Exception as e:
        print("Supabase threw an error:", e)
        raise

def sign_up(email: str, password: str, display_name: str, geo_alert: bool):
    try:
        # Register the user (add to auth.users)
        res = supabase.auth.sign_up(
            {"email": email,
            "password": password
             }
        )
        user = res.user
        session = res.session

        if not user or not session:
            raise Exception("No user/session returned from Supabase")

        access_token = session.access_token
        supabase.postgrest.auth(access_token) # Authorize user
        user_id = user.id

        # Add extra profile details to user_profiles
        profile_res = supabase.from_("user_profiles").insert({
            "user_id": user_id,
            "display_name": display_name,
            "geo_alert": geo_alert
        }).execute()
        print(profile_res)

        try:
            # if there is an error
            raise Exception(profile_res.error.message)
        except AttributeError:
            pass

        return user

    except Exception as e:
        print("Supabase threw an error:", e)
        raise

