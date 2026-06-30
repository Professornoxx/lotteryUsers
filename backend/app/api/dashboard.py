from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
def summary():
    # TODO: total users, active, deposits, withdrawals
    return {}


@router.get("/registrations-over-time")
def registrations_over_time():
    return []


@router.get("/top-cities")
def top_cities():
    return []


@router.get("/agent-funnel")
def agent_funnel():
    return []


@router.get("/balance-distribution")
def balance_distribution():
    return []


@router.get("/member-levels")
def member_levels():
    return []


@router.get("/platform-split")
def platform_split():
    return []
