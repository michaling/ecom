from fastapi import APIRouter, HTTPException
from auth.schemas import SignInData, SignUpData
from auth.logic import sign_in, sign_up
from gotrue.errors import AuthError
from supabase_client import supabase
from pydantic import BaseModel


router = APIRouter()

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/signin")
def signin_endpoint(data: SignInData):
    try:
        user, session = sign_in(data.email, data.password)
        print(f"[LOGIN] {user.email} signed in.")
        return {"message": "Sign-in successful", "user_id": user.id, "access_token": session.access_token}
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

