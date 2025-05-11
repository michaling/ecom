from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.auth.routes import router as auth_router

app = FastAPI()
app.include_router(auth_router, prefix="/auth")


@app.get("/")
async def root():
    return {"message": "Hello World2"}