from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, query, query_one
from app.api.auth import get_current_admin

router = APIRouter()


@router.get("/summary")
def summary(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query_one(db, """
        SELECT
            COUNT(u.user_id)                                    AS total_users,
            SUM(CASE WHEN u.user_status = 0 THEN 1 END)        AS active_users,
            SUM(CASE WHEN u.user_status = 1 THEN 1 END)        AS banned_users,
            SUM(CASE WHEN u.is_test = 1 THEN 1 END)            AS test_users,
            SUM(CASE WHEN ua.agent_status = 3 THEN 1 END)      AS approved_agents,
            COALESCE(SUM(f.total_deposits), 0)                 AS total_deposits,
            COALESCE(SUM(f.total_withdrawals), 0)              AS total_withdrawals,
            COALESCE(SUM(f.balance), 0)                        AS total_balance,
            COALESCE(SUM(f.frozen_amount), 0)                  AS total_frozen,
            ROUND(COALESCE(AVG(f.total_deposits), 0)::numeric, 2) AS avg_deposit,
            COALESCE(SUM(f.recharge_count), 0)                 AS total_recharges
        FROM users u
        LEFT JOIN user_financials f ON f.user_id = u.user_id
        LEFT JOIN user_agents ua ON ua.user_id = u.user_id
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
