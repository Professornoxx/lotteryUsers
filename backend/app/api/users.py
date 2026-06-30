from fastapi import APIRouter, Query, HTTPException, Depends
from app.core.database import get_connection
from app.api.auth import get_current_admin

router = APIRouter()


@router.get("/")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
    search: str = Query(None),
    city: str = Query(None),
    status: int = Query(None),
    agent_status: int = Query(None),
    reg_channel: str = Query(None),
    reg_source: str = Query(None),
    min_deposit: float = Query(None),
    max_deposit: float = Query(None),
    _=Depends(get_current_admin),
):
    conn = get_connection()
    try:
        cur = conn.cursor()
        where = ["1=1"]
        params = {}

        if search:
            where.append("(u.username LIKE :search OR u.phone LIKE :search)")
            params["search"] = f"%{search}%"
        if city:
            where.append("u.city = :city")
            params["city"] = city
        if status is not None:
            where.append("u.user_status = :status")
            params["status"] = status
        if reg_channel:
            where.append("u.reg_channel = :reg_channel")
            params["reg_channel"] = reg_channel
        if reg_source:
            where.append("u.reg_source = :reg_source")
            params["reg_source"] = reg_source
        if agent_status is not None:
            where.append("ua.agent_status = :agent_status")
            params["agent_status"] = agent_status
        if min_deposit is not None:
            where.append("f.total_deposits >= :min_deposit")
            params["min_deposit"] = min_deposit
        if max_deposit is not None:
            where.append("f.total_deposits <= :max_deposit")
            params["max_deposit"] = max_deposit

        where_sql = " AND ".join(where)

        count_sql = f"""
            SELECT COUNT(*) FROM USERS u
            LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
            LEFT JOIN USER_AGENTS ua ON ua.user_id = u.user_id
            WHERE {where_sql}
        """
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

        offset = (page - 1) * page_size
        params["offset"] = offset
        params["page_size"] = page_size

        data_sql = f"""
            SELECT * FROM (
                SELECT
                    u.user_id, u.username, u.phone, u.email, u.city,
                    u.gender, u.user_status, u.is_test,
                    u.reg_channel, u.reg_source, u.create_time,
                    f.balance, f.total_deposits, f.total_withdrawals,
                    f.frozen_amount, f.recharge_count,
                    ua.agent_status, ua.agent_level, ua.member_level,
                    d.last_active_time,
                    ROW_NUMBER() OVER (ORDER BY u.create_time DESC) AS rn
                FROM USERS u
                LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
                LEFT JOIN USER_AGENTS ua ON ua.user_id = u.user_id
                LEFT JOIN USER_DEVICES d ON d.user_id = u.user_id
                WHERE {where_sql}
            ) WHERE rn > :offset AND rn <= :offset + :page_size
        """
        cur.execute(data_sql, params)
        cols = [d[0].lower() for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        return {"page": page, "page_size": page_size, "total": total, "data": rows}
    finally:
        conn.close()


@router.get("/{user_id}")
def get_user(user_id: int, _=Depends(get_current_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                u.*, f.balance, f.user_balance, f.total_deposits,
                f.total_withdrawals, f.frozen_amount, f.withdraw_limit, f.recharge_count,
                ua.agent_status, ua.agent_level, ua.member_level,
                ua.parent_user_id, ua.inviter_user_id,
                d.register_device, d.login_device, d.device_id, d.last_active_time,
                i.im_user_id, i.im_user_status, i.group_name,
                fu.flow_up_time, fu.next_flow_up_time
            FROM USERS u
            LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
            LEFT JOIN USER_AGENTS ua ON ua.user_id = u.user_id
            LEFT JOIN USER_DEVICES d ON d.user_id = u.user_id
            LEFT JOIN USER_IM i ON i.user_id = u.user_id
            LEFT JOIN USER_FOLLOWUP fu ON fu.user_id = u.user_id
            WHERE u.user_id = :1
        """, [user_id])
        cols = [d[0].lower() for d in cur.description]
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(zip(cols, row))
    finally:
        conn.close()


@router.get("/{user_id}/referrals")
def get_referrals(user_id: int, _=Depends(get_current_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.user_id, u.username, u.phone, u.city, u.create_time,
                   f.total_deposits, f.balance
            FROM USERS u
            LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
            LEFT JOIN USER_AGENTS ua ON ua.user_id = u.user_id
            WHERE ua.inviter_user_id = :1
            ORDER BY u.create_time DESC
        """, [user_id])
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()
