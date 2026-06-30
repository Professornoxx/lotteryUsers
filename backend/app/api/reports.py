from fastapi import APIRouter, Query, Depends
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


@router.get("/top-depositors")
def top_depositors(limit: int = Query(20, le=100), _=Depends(get_current_admin)):
    return query(f"""
        SELECT u.user_id, u.username, u.phone, u.city,
               f.total_deposits, f.recharge_count, f.balance
        FROM USERS u
        JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        WHERE f.total_deposits > 0
        ORDER BY f.total_deposits DESC
        FETCH FIRST {limit} ROWS ONLY
    """)


@router.get("/top-withdrawals")
def top_withdrawals(limit: int = Query(20, le=100), _=Depends(get_current_admin)):
    return query(f"""
        SELECT u.user_id, u.username, u.phone, u.city,
               f.total_withdrawals, f.total_deposits, f.balance
        FROM USERS u
        JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        WHERE f.total_withdrawals > 0
        ORDER BY f.total_withdrawals DESC
        FETCH FIRST {limit} ROWS ONLY
    """)


@router.get("/inactive-users")
def inactive_users(days: int = Query(7), _=Depends(get_current_admin)):
    return query("""
        SELECT u.user_id, u.username, u.phone, u.city,
               d.last_active_time, f.balance, f.total_deposits
        FROM USERS u
        JOIN USER_DEVICES d ON d.user_id = u.user_id
        JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        WHERE d.last_active_time < SYSTIMESTAMP - :1
          AND u.user_status = 0
        ORDER BY d.last_active_time ASC
        FETCH FIRST 100 ROWS ONLY
    """, [days])


@router.get("/agent-performance")
def agent_performance(_=Depends(get_current_admin)):
    return query("""
        SELECT
            ua.user_id AS agent_id,
            u.username,
            u.city,
            ua.agent_level,
            COUNT(ref.user_id) AS referrals,
            NVL(SUM(rf.total_deposits), 0) AS referred_deposits
        FROM USER_AGENTS ua
        JOIN USERS u ON u.user_id = ua.user_id
        LEFT JOIN USER_AGENTS ref ON ref.inviter_user_id = ua.user_id
        LEFT JOIN USER_FINANCIALS rf ON rf.user_id = ref.user_id
        WHERE ua.agent_status = 3
        GROUP BY ua.user_id, u.username, u.city, ua.agent_level
        ORDER BY referrals DESC
        FETCH FIRST 50 ROWS ONLY
    """)


@router.get("/channel-performance")
def channel_performance(_=Depends(get_current_admin)):
    return query("""
        SELECT
            NVL(u.reg_channel, 'Unknown') AS channel,
            COUNT(u.user_id)              AS user_count,
            NVL(SUM(f.total_deposits), 0) AS total_deposits,
            ROUND(NVL(AVG(f.total_deposits), 0), 2) AS avg_deposit,
            ROUND(NVL(AVG(f.balance), 0), 2) AS avg_balance,
            SUM(CASE WHEN f.total_deposits > 0 THEN 1 ELSE 0 END) AS deposited_users
        FROM USERS u
        LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        GROUP BY u.reg_channel
        ORDER BY total_deposits DESC
    """)


@router.get("/zero-deposit-users")
def zero_deposit_users(_=Depends(get_current_admin)):
    return query("""
        SELECT u.user_id, u.username, u.phone, u.city,
               u.reg_channel, u.create_time, d.last_active_time
        FROM USERS u
        JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        LEFT JOIN USER_DEVICES d ON d.user_id = u.user_id
        WHERE f.total_deposits = 0
          AND u.is_test = 0
        ORDER BY u.create_time DESC
        FETCH FIRST 100 ROWS ONLY
    """)


@router.get("/high-balance-users")
def high_balance_users(limit: int = Query(20, le=100), _=Depends(get_current_admin)):
    return query(f"""
        SELECT u.user_id, u.username, u.phone, u.city,
               f.balance, f.total_deposits, f.total_withdrawals, f.frozen_amount
        FROM USERS u
        JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        ORDER BY f.balance DESC
        FETCH FIRST {limit} ROWS ONLY
    """)


@router.get("/city-financials")
def city_financials(_=Depends(get_current_admin)):
    return query("""
        SELECT
            NVL(u.city, 'Unknown') AS city,
            COUNT(u.user_id) AS user_count,
            NVL(SUM(f.total_deposits), 0) AS total_deposits,
            NVL(SUM(f.total_withdrawals), 0) AS total_withdrawals,
            ROUND(NVL(AVG(f.balance), 0), 2) AS avg_balance
        FROM USERS u
        LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        GROUP BY u.city
        ORDER BY total_deposits DESC
        FETCH FIRST 20 ROWS ONLY
    """)


@router.get("/new-users-summary")
def new_users_summary(_=Depends(get_current_admin)):
    return query("""
        SELECT
            TRUNC(u.create_time, 'DD') AS date,
            COUNT(*) AS new_users,
            SUM(CASE WHEN f.total_deposits > 0 THEN 1 ELSE 0 END) AS deposited,
            NVL(SUM(f.total_deposits), 0) AS total_deposits
        FROM USERS u
        LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
        WHERE u.create_time IS NOT NULL
        GROUP BY TRUNC(u.create_time, 'DD')
        ORDER BY 1 DESC
        FETCH FIRST 30 ROWS ONLY
    """)
