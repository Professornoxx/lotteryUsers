from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, query, query_one
from app.api.auth import get_current_admin

router = APIRouter()


@router.get("/summary")
def summary(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query_one(db, """
        SELECT
            (SELECT COUNT(*) FROM users)                          AS total_users,
            (SELECT COUNT(*) FROM users WHERE user_status = 0)   AS active_users,
            (SELECT COUNT(*) FROM users WHERE user_status = 1)   AS banned_users,
            (SELECT COUNT(*) FROM users WHERE is_test = 1)       AS test_users,
            (SELECT COALESCE(SUM(amount),0) FROM deposits)       AS total_deposits,
            (SELECT COALESCE(SUM(amount),0) FROM withdrawals)    AS total_withdrawals,
            (SELECT COALESCE(SUM(balance),0) FROM wallet_details) AS total_balance,
            (SELECT COUNT(*) FROM deposits)                       AS total_recharges,
            0                                                     AS approved_agents,
            0                                                     AS total_frozen,
            0                                                     AS avg_deposit
    """)


@router.get("/registrations-over-time")
def registrations_over_time(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT DATE_TRUNC('day', create_time) AS date, COUNT(*) AS count
        FROM users WHERE create_time IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """)


@router.get("/top-cities")
def top_cities(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT COALESCE(city, 'Unknown') AS city, COUNT(*) AS count
        FROM users GROUP BY city ORDER BY count DESC LIMIT 15
    """)


@router.get("/agent-funnel")
def agent_funnel(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT
            CASE agent_status
                WHEN 0 THEN 'Not Applied'
                WHEN 1 THEN 'Pending'
                WHEN 2 THEN 'Rejected'
                WHEN 3 THEN 'Approved'
                ELSE 'Unknown'
            END AS status,
            COUNT(*) AS count
        FROM user_agents
        WHERE agent_status IS NOT NULL
        GROUP BY agent_status ORDER BY agent_status
    """)


@router.get("/balance-distribution")
def balance_distribution(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT
            CASE
                WHEN balance = 0    THEN '0'
                WHEN balance < 100  THEN '1-100'
                WHEN balance < 500  THEN '100-500'
                WHEN balance < 1000 THEN '500-1000'
                WHEN balance < 5000 THEN '1000-5000'
                ELSE '5000+'
            END AS range,
            COUNT(*) AS count
        FROM user_financials
        GROUP BY 1 ORDER BY MIN(balance)
    """)


@router.get("/member-levels")
def member_levels(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT 'Level ' || COALESCE(member_level::text, 'Unknown') AS level,
               COUNT(*) AS count
        FROM user_agents GROUP BY member_level ORDER BY member_level
    """)


@router.get("/platform-split")
def platform_split(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT COALESCE(reg_source, 'Unknown') AS platform, COUNT(*) AS count
        FROM users GROUP BY reg_source ORDER BY count DESC
    """)


@router.get("/channel-split")
def channel_split(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT COALESCE(reg_channel, 'Unknown') AS channel, COUNT(*) AS count
        FROM users GROUP BY reg_channel ORDER BY count DESC
    """)


@router.get("/deposit-distribution")
def deposit_distribution(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT
            CASE
                WHEN total_deposits = 0     THEN 'No Deposit'
                WHEN total_deposits < 500   THEN '1-500'
                WHEN total_deposits < 1000  THEN '500-1000'
                WHEN total_deposits < 5000  THEN '1000-5000'
                WHEN total_deposits < 10000 THEN '5000-10000'
                ELSE '10000+'
            END AS range,
            COUNT(*) AS count
        FROM user_financials GROUP BY 1 ORDER BY MIN(total_deposits)
    """)


@router.get("/im-status")
def im_status(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT COALESCE(im_user_status, 'Unknown') AS status, COUNT(*) AS count
        FROM user_im GROUP BY im_user_status ORDER BY count DESC
    """)


@router.get("/daily-active-users")
def daily_active_users(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT DATE_TRUNC('day', last_active_time) AS date, COUNT(*) AS count
        FROM user_devices WHERE last_active_time IS NOT NULL
        GROUP BY 1 ORDER BY 1 DESC LIMIT 30
    """)
