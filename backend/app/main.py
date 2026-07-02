from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import auth, users, dashboard, reports, export, pipeline
from app.core.database import SessionLocal
from app.services.pipeline_sync import sync_all
import threading, time


def scheduler_loop():
    """Background thread: sync every 20 minutes if token is set."""
    while True:
        time.sleep(20 * 60)  # wait 20 minutes
        try:
            db = SessionLocal()
            sync_all(db)
            db.close()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start 20-minute sync scheduler as daemon thread
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    yield


app = FastAPI(title="Lottery Users API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(users.router,    prefix="/api/users",    tags=["Users"])
app.include_router(dashboard.router,prefix="/api/dashboard",tags=["Dashboard"])
app.include_router(reports.router,  prefix="/api/reports",  tags=["Reports"])
app.include_router(export.router,   prefix="/api/export",   tags=["Export"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Pipeline"])


@app.get("/")
def root():
    return {"status": "ok", "message": "Lottery Users API is running"}
