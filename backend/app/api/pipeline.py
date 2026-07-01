from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.core.database import get_db
from app.api.auth import get_current_admin
from app.services.pipeline_sync import sync_all

router = APIRouter()


class TokenIn(BaseModel):
    bearer_token: str


@router.post("/token/")
def save_token(body: TokenIn, background: BackgroundTasks,
               db: Session = Depends(get_db),
               _=Depends(get_current_admin)):
    db.execute(text(
        "UPDATE pipeline_config SET bearer_token=:t WHERE id=1"
    ), {"t": body.bearer_token})
    db.commit()
    # Trigger sync immediately in background
    background.add_task(sync_all, db)
    return {"message": "Token saved. Sync started in background."}


@router.post("/sync/")
def manual_sync(background: BackgroundTasks,
                db: Session = Depends(get_db),
                _=Depends(get_current_admin)):
    background.add_task(sync_all, db)
    return {"message": "Sync started"}


@router.get("/status/")
def get_status(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    from app.core.database import query_one
    row = query_one(db, "SELECT last_sync, last_status, bearer_token FROM pipeline_config WHERE id=1", {})
    has_token = bool(row and row.get("bearer_token"))
    return {
        "has_token": has_token,
        "last_sync": row["last_sync"] if row else None,
        "last_status": row["last_status"] if row else None,
    }
