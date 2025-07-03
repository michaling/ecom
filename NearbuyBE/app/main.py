import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from auth.routes import router as auth_router
from lists.lists import router as lists_router, fetch_and_store_recommendations
from lists.items import router as items_router
from lists.cleanup import router as lists_cleanup_router
from profile.profile import router as profile_router
from alerts_tab.alerts_tab import router as alerts_tab_router
from notifications.main import router as notifications_router
from supabase_client import supabase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

app = FastAPI()

# Register routers
app.include_router(auth_router, prefix="/auth")
app.include_router(lists_router)
app.include_router(lists_cleanup_router)
app.include_router(items_router)
app.include_router(profile_router)
app.include_router(alerts_tab_router)
app.include_router(notifications_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "https://yvxcfsw-anonymous-8081.exp.direct",
        "http://yvxcfsw-anonymous-8081.exp.direct",
        "http://10.0.0.49:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Scheduler Setup ----------------
async def refresh_all_recommendations():
    """Fetch all active lists and update ML suggestions."""
    lists_data = (
        supabase.table("lists")
        .select("list_id", "name")
        .eq("is_deleted", False)
        .execute()
        .data or []
    )
    for lst in lists_data:
        fetch_and_store_recommendations(lst["name"], lst["list_id"])

@app.on_event("startup")
def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Schedule at midnight and noon UTC
    scheduler.add_job(
        lambda: asyncio.create_task(refresh_all_recommendations()),
        trigger="cron",
        hour="0,12"
    )
    scheduler.start()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
