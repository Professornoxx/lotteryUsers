from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    search: str = Query(None),
    city: str = Query(None),
    status: int = Query(None),
    agent_status: int = Query(None),
):
    # TODO: Query Oracle DB
    return {"page": page, "page_size": page_size, "total": 0, "data": []}


@router.get("/{user_id}")
def get_user(user_id: int):
    # TODO: Query Oracle DB
    return {"user_id": user_id}
