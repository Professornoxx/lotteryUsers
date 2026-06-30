from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import verify_password, create_access_token

router = APIRouter()

# TODO: Replace with real DB lookup
ADMIN_USER = {"username": "admin", "password_hash": "$2b$12$placeholder"}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    # Placeholder — wire to Oracle DB in next step
    if form.username != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": form.username})
    return {"access_token": token, "token_type": "bearer"}
