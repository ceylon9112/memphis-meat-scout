from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from .database import connect_db, close_db
from .routers import deals, cuts, vendors, weather
from .routers.admin import auth as admin_auth, dashboard, deals as admin_deals
from .routers.admin import vendors as admin_vendors, cuts as admin_cuts, staging
from .seed import seed_database
from .services.discovery import run_discovery

load_dotenv()

app = FastAPI(title="Memphis Meat Scout API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup():
    await connect_db()
    await seed_database()
    # Schedule daily discovery at 6:00 AM
    _scheduler.add_job(run_discovery, "cron", hour=6, minute=0, id="daily_discovery")
    _scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    _scheduler.shutdown(wait=False)
    await close_db()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Public routes
app.include_router(deals.router,   prefix="/api", tags=["public"])
app.include_router(cuts.router,    prefix="/api", tags=["public"])
app.include_router(vendors.router, prefix="/api", tags=["public"])
app.include_router(weather.router, prefix="/api", tags=["public"])

# Admin routes
app.include_router(admin_auth.router,    prefix="/api/admin", tags=["admin"])
app.include_router(dashboard.router,     prefix="/api/admin", tags=["admin"])
app.include_router(admin_deals.router,   prefix="/api/admin", tags=["admin"])
app.include_router(admin_vendors.router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_cuts.router,    prefix="/api/admin", tags=["admin"])
app.include_router(staging.router,       prefix="/api/admin", tags=["admin"])
