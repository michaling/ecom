from pydantic import BaseModel

class SignInData(BaseModel):
    email: str
    password: str

class SignUpData(BaseModel):
    email: str
    password: str
    display_name: str
    geo_alert: bool