from fastapi import APIRouter, HTTPException
from .schemas import SignInData, SignUpData
from .logic import sign_in, sign_up
from gotrue.errors import AuthError

router = APIRouter()

@router.post("/signin")
def signin_endpoint(data: SignInData):
    try:
        user, session = sign_in(data.email, data.password)
        print(f"[LOGIN] {user.email} signed in.")
        return {"message": "Sign-in successful", "user_id": user.id, "access_token": session.access_token}
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/signup")
def signup_endpoint(data: SignUpData):
    try:
        user, session = sign_up(
            email=data.email,
            password=data.password,
            display_name=data.display_name,
            geo_alert=data.geo_alert,
        )
        print(f"[SIGNUP] {user.email} created.")
        return {"message": "Sign-up successful", "user_id": user.id, "access_token": session.access_token}
    except AuthError as e:
        print("Supabase AuthError:", e)
        raise HTTPException(status_code=400, detail=str(e))
