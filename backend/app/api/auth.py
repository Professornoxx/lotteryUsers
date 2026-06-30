from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core.security import verify_password, create_access_token, decode_token
from app.core.database import get_connection

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_admin(username: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT admin_id, username, password_hash, role FROM ADMIN_USERS WHERE username = :1",
            [username],
        )
        row = cur.fetchone()
        if row:
            return {"admin_id": row[0], "username": row[1], "password_hash": row[2], "role": row[3]}
        return None
    finally:
        conn.close()


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    admin = get_admin(form.username)
    if not admin or not verify_password(form.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": admin["username"], "role": admin["role"]})
    return {"access_token": token, "token_type": "bearer"}


def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
