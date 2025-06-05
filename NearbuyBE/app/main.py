from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.auth.routes import router as auth_router
from app.lists.lists import router as lists_router
from app.lists.items import router as items_router
from app.lists.cleanup import router as lists_cleanup_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],  # Replace with your frontend URL in production
    allow_origins=[
        "http://localhost:8081",
        "https://yvxcfsw-anonymous-8081.exp.direct",
        "http://yvxcfsw-anonymous-8081.exp.direct",
        "http://10.0.0.49:8000"
    ],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(lists_router)
app.include_router(lists_cleanup_router)
app.include_router(items_router)
