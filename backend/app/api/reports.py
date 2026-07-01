from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db, query
from app.api.auth import get_current_admin

router = APIRouter()


@router.get("/top-depositors")
def top_depositors(limit: int = Query(20, le=100), db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, f"""
        SELECT u.user_id, u.username, u.phone, u.city,
               f.total_deposits, f.recharge_count, f.balance
        FROM users u JOIN user_financials f ON f.user_id = u.user_id
        WHERE f.total_deposits > 0
        ORDER BY f.total_deposits DESC LIMIT {limit}
    """)


@router.get("/top-withdrawals")
def top_withdrawals(limit: int = Query(20, le=100), db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, f"""
        SELECT u.user_id, u.username, u.phone, u.city,
               f.total_withdrawals, f.total_deposits, f.balance
        FROM users u JOIN user_financials f ON f.user_id = u.user_id
        WHERE f.total_withdrawals > 0
        ORDER BY f.total_withdrawals DESC LIMIT {limit}
    """)


@router.get("/inactive-users")
def inactive_users(days: int = Query(7), db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT u.user_id, u.username, u.phone, u.city,
               d.last_active_time, f.balance, f.total_deposits
        FROM users u
        JOIN user_devices d ON d.user_id = u.user_id
        JOIN user_financials f ON f.user_id = u.user_id
        WHERE d.last_active_time < NOW() - INTERVAL '1 day' * :days
          AND u.user_status = 0
        ORDER BY d.last_active_time ASC LIMIT 100
    """, {"days": days})


@router.get("/agent-performance")
def agent_performance(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT ua.user_id AS agent_id, u.username, u.city, ua.agent_level,
               COUNT(ref.user_id) AS referrals,
               COALESCE(SUM(rf.total_deposits), 0) AS referred_deposits
        FROM user_agents ua
        JOIN users u ON u.user_id = ua.user_id
        LEFT JOIN user_agents ref ON ref.inviter_user_id = ua.user_id
        LEFT JOIN user_financials rf ON rf.user_id = ref.user_id
        WHERE ua.agent_status = 3
        GROUP BY ua.user_id, u.username, u.city, ua.agent_level
        ORDER BY referrals DESC LIMIT 50
    """)


@router.get("/channel-performance")
def channel_performance(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT COALESCE(u.reg_channel, 'Unknown') AS channel,
               COUNT(u.user_id) AS user_count,
               COALESCE(SUM(f.total_deposits), 0) AS total_deposits,
               ROUND(COALESCE(AVG(f.total_deposits), 0)::numeric, 2) AS avg_deposit,
               ROUND(COALESCE(AVG(f.balance), 0)::numeric, 2) AS avg_balance,
               SUM(CASE WHEN f.total_deposits > 0 THEN 1 ELSE 0 END) AS deposited_users
        FROM users u LEFT JOIN user_financials f ON f.user_id = u.user_id
        GROUP BY u.reg_channel ORDER BY total_deposits DESC
    """)


@router.get("/zero-deposit-users")
def zero_deposit_users(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT u.user_id, u.username, u.phone, u.city,
               u.reg_channel, u.create_time, d.last_active_time
        FROM users u
        JOIN user_financials f ON f.user_id = u.user_id
        LEFT JOIN user_devices d ON d.user_id = u.user_id
        WHERE f.total_deposits = 0 AND u.is_test = 0
        ORDER BY u.create_time DESC LIMIT 100
    """)


@router.get("/high-balance-users")
def high_balance_users(limit: int = Query(20, le=100), db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, f"""
        SELECT u.user_id, u.username, u.phone, u.city,
               f.balance, f.total_deposits, f.total_withdrawals, f.frozen_amount
        FROM users u JOIN user_financials f ON f.user_id = u.user_id
        ORDER BY f.balance DESC LIMIT {limit}
    """)


@router.get("/city-financials")
def city_financials(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT COALESCE(u.city, 'Unknown') AS city,
               COUNT(u.user_id) AS user_count,
               COALESCE(SUM(f.total_deposits), 0) AS total_deposits,
               COALESCE(SUM(f.total_withdrawals), 0) AS total_withdrawals,
               ROUND(COALESCE(AVG(f.balance), 0)::numeric, 2) AS avg_balance
        FROM users u LEFT JOIN user_financials f ON f.user_id = u.user_id
        GROUP BY u.city ORDER BY total_deposits DESC LIMIT 20
    """)


@router.get("/new-users-summary")
def new_users_summary(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return query(db, """
        SELECT DATE_TRUNC('day', u.create_time) AS date,
               COUNT(*) AS new_users,
               SUM(CASE WHEN f.total_deposits > 0 THEN 1 ELSE 0 END) AS deposited,
               COALESCE(SUM(f.total_deposits), 0) AS total_deposits
        FROM users u LEFT JOIN user_financials f ON f.user_id = u.user_id
        WHERE u.create_time IS NOT NULL
        GROUP BY 1 ORDER BY 1 DESC LIMIT 30
    """)
