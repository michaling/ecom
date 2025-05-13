from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.auth.routes import router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/auth")
