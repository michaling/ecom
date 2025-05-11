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

def sign_up(email: str, password: str):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return res.user

    except Exception as e:
        print("Supabase threw an error:", e)
        raise

