from fastapi import APIRouter, HTTPException
from app.auth.schemas import SignInData, SignUpData
from app.auth.logic import sign_in, sign_up
from gotrue.errors import AuthError

router = APIRouter()

@router.post("/signin")
def signin_endpoint(data: SignInData):
    try:
        user = sign_in(data.email, data.password)
        print(f"[LOGIN] {user.email} signed in.")
        return {"message": "Sign-in successful", "user_id": user.id}
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/signup")
def signup_endpoint(data: SignUpData):
    try:
        user = sign_up(data.email, data.password)
        print(f"[SIGNUP] {user.email} created.")
        return {"message": "Sign-up successful", "user_id": user.id}
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/test")
def test():
    print("✅ HIT /test")
    return "test"
