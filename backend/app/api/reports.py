from fastapi import APIRouter

router = APIRouter()


@router.get("/top-depositors")
def top_depositors():
    return []


@router.get("/inactive-users")
def inactive_users():
    return []


@router.get("/agent-performance")
def agent_performance():
    return []


@router.get("/channel-performance")
def channel_performance():
    return []
