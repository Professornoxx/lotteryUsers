from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import verify_password, create_access_token, decode_token
from app.core.database import get_db, query_one

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = query_one(db,
        "SELECT admin_id, username, password_hash, role FROM admin_users WHERE username = :u",
        {"u": form.username}
    )
    if not admin or not verify_password(form.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": admin["username"], "role": admin["role"]})
    return {"access_token": token, "token_type": "bearer"}


def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        return decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
