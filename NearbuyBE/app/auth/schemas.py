from pydantic import BaseModel

class SignInData(BaseModel):
    email: str
    password: str

class SignUpData(BaseModel):
    email: str
    password: str
    phone: str | None = None