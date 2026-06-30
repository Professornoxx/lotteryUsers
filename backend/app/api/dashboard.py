from fastapi import APIRouter, Depends
from app.core.database import get_connection
from app.api.auth import get_current_admin

router = APIRouter()


def query(sql, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def query_one(sql, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        cols = [d[0].lower() for d in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else {}
    finally:
        conn.close()


@router.get("/summary")
def summary(_=Depends(get_current_admin)):
    return query_one("""
        SELECT
            COUNT(u.user_id)                              AS total_users,
            SUM(CASE WHEN u.user_status = 0 THEN 1 END)  AS active_users,
            SUM(CASE WHEN u.user_status = 1 THEN 1 END)  AS banned_users,
            SUM(CASE WHEN u.is_test = 1 THEN 1 END)      AS test_users,
            SUM(CASE WHEN ua.agent_status = 3 THEN 1 END) AS approved_agents,
            SUM(f.total_deposits)                         AS total_deposits,
            SUM(f.total_withdrawals)                      AS total_withdrawals,
            SUM(f.balance)                                AS total_balance,
            SUM(f.frozen_amount)                          AS total_frozen,
            ROUND(AVG(f.total_deposits), 2)               AS avg_deposit,
            SUM(f.recharge_count)                         AS total_recharges
        FROM USERS u
        LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        LEFT JOIN USER_AGENTS ua ON ua.user_id = u.user_id
    """)


@router.get("/registrations-over-time")
def registrations_over_time(_=Depends(get_current_admin)):
    return query("""
        SELECT
            TRUNC(create_time, 'DD') AS date,
            COUNT(*) AS count
        FROM USERS
        WHERE create_time IS NOT NULL
        GROUP BY TRUNC(create_time, 'DD')
        ORDER BY 1
    """)


@router.get("/top-cities")
def top_cities(_=Depends(get_current_admin)):
    return query("""
        SELECT city, COUNT(*) AS count
        FROM USERS
        WHERE city IS NOT NULL
        GROUP BY city
        ORDER BY count DESC
        FETCH FIRST 15 ROWS ONLY
    """)


@router.get("/agent-funnel")
def agent_funnel(_=Depends(get_current_admin)):
    return query("""
        SELECT
            CASE agent_status
                WHEN 0 THEN 'Not Applied'
                WHEN 1 THEN 'Pending'
                WHEN 2 THEN 'Rejected'
                WHEN 3 THEN 'Approved'
                ELSE 'Unknown'
            END AS status,
            COUNT(*) AS count
        FROM USER_AGENTS
        WHERE agent_status IS NOT NULL
        GROUP BY agent_status
        ORDER BY agent_status
    """)


@router.get("/balance-distribution")
def balance_distribution(_=Depends(get_current_admin)):
    return query("""
        SELECT
            CASE
                WHEN balance = 0           THEN '0'
                WHEN balance < 100         THEN '1-100'
                WHEN balance < 500         THEN '100-500'
                WHEN balance < 1000        THEN '500-1000'
                WHEN balance < 5000        THEN '1000-5000'
                ELSE '5000+'
            END AS range,
            COUNT(*) AS count
        FROM USER_FINANCIALS
        GROUP BY
            CASE
                WHEN balance = 0           THEN '0'
                WHEN balance < 100         THEN '1-100'
                WHEN balance < 500         THEN '100-500'
                WHEN balance < 1000        THEN '500-1000'
                WHEN balance < 5000        THEN '1000-5000'
                ELSE '5000+'
            END
        ORDER BY MIN(balance)
    """)


@router.get("/member-levels")
def member_levels(_=Depends(get_current_admin)):
    return query("""
        SELECT
            'Level ' || NVL(TO_CHAR(member_level), 'Unknown') AS level,
            COUNT(*) AS count
        FROM USER_AGENTS
        GROUP BY member_level
        ORDER BY member_level
    """)


@router.get("/platform-split")
def platform_split(_=Depends(get_current_admin)):
    return query("""
        SELECT
            NVL(reg_source, 'Unknown') AS platform,
            COUNT(*) AS count
        FROM USERS
        GROUP BY reg_source
        ORDER BY count DESC
    """)


@router.get("/channel-split")
def channel_split(_=Depends(get_current_admin)):
    return query("""
        SELECT
            NVL(reg_channel, 'Unknown') AS channel,
            COUNT(*) AS count
        FROM USERS
        GROUP BY reg_channel
        ORDER BY count DESC
    """)


@router.get("/deposit-distribution")
def deposit_distribution(_=Depends(get_current_admin)):
    return query("""
        SELECT
            CASE
                WHEN total_deposits = 0      THEN 'No Deposit'
                WHEN total_deposits < 500    THEN '1-500'
                WHEN total_deposits < 1000   THEN '500-1000'
                WHEN total_deposits < 5000   THEN '1000-5000'
                WHEN total_deposits < 10000  THEN '5000-10000'
                ELSE '10000+'
            END AS range,
            COUNT(*) AS count
        FROM USER_FINANCIALS
        GROUP BY
            CASE
                WHEN total_deposits = 0      THEN 'No Deposit'
                WHEN total_deposits < 500    THEN '1-500'
                WHEN total_deposits < 1000   THEN '500-1000'
                WHEN total_deposits < 5000   THEN '1000-5000'
                WHEN total_deposits < 10000  THEN '5000-10000'
                ELSE '10000+'
            END
        ORDER BY MIN(total_deposits)
    """)


@router.get("/im-status")
def im_status(_=Depends(get_current_admin)):
    return query("""
        SELECT
            NVL(im_user_status, 'Unknown') AS status,
            COUNT(*) AS count
        FROM USER_IM
        GROUP BY im_user_status
        ORDER BY count DESC
    """)


@router.get("/daily-active-users")
def daily_active_users(_=Depends(get_current_admin)):
    return query("""
        SELECT
            TRUNC(last_active_time, 'DD') AS date,
            COUNT(*) AS count
        FROM USER_DEVICES
        WHERE last_active_time IS NOT NULL
        GROUP BY TRUNC(last_active_time, 'DD')
        ORDER BY 1
        FETCH FIRST 30 ROWS ONLY
    """)
