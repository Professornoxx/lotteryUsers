from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
from app.core.database import get_connection
from app.api.auth import get_current_admin
from app.schemas.user import UserCreate, UserUpdate
from app.services.excel_sync import regenerate_excel
from datetime import datetime

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────

def run_query(sql, params=None, fetch=True):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        if fetch:
            cols = [d[0].lower() for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        conn.commit()
    finally:
        conn.close()


def next_user_id() -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT NVL(MAX(user_id), 100000) + 1 FROM USERS")
        return cur.fetchone()[0]
    finally:
        conn.close()


# ── LIST ───────────────────────────────────────────────────

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

        cur.execute(f"""
            SELECT COUNT(*) FROM USERS u
            LEFT JOIN USER_FINANCIALS f ON f.user_id = u.user_id
            LEFT JOIN USER_AGENTS ua ON ua.user_id = u.user_id
            WHERE {where_sql}
        """, params)
        total = cur.fetchone()[0]

        offset = (page - 1) * page_size
        params["offset"] = offset
        params["page_size"] = page_size

        cur.execute(f"""
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
        """, params)
        cols = [d[0].lower() for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return {"page": page, "page_size": page_size, "total": total, "data": rows}
    finally:
        conn.close()


# ── GET ONE ────────────────────────────────────────────────

@router.get("/{user_id}")
def get_user(user_id: int, _=Depends(get_current_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.*, f.balance, f.user_balance, f.total_deposits,
                f.total_withdrawals, f.frozen_amount, f.withdraw_limit, f.recharge_count,
                ua.agent_status, ua.agent_level, ua.member_level,
                ua.parent_user_id, ua.inviter_user_id,
                ua.agent_level1, ua.agent_level2, ua.agent_level3, ua.agent_level4,
                d.register_device, d.login_device, d.last_login_device,
                d.device_id, d.push_token, d.last_active_time,
                i.im_user_id, i.im_user_status, i.im_customer, i.group_name, i.adjust_adid,
                fu.flow_up_time, fu.next_flow_up_time
            FROM USERS u
            LEFT JOIN USER_FINANCIALS f  ON f.user_id  = u.user_id
            LEFT JOIN USER_AGENTS ua     ON ua.user_id = u.user_id
            LEFT JOIN USER_DEVICES d     ON d.user_id  = u.user_id
            LEFT JOIN USER_IM i          ON i.user_id  = u.user_id
            LEFT JOIN USER_FOLLOWUP fu   ON fu.user_id = u.user_id
            WHERE u.user_id = :1
        """, [user_id])
        cols = [d[0].lower() for d in cur.description]
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(zip(cols, row))
    finally:
        conn.close()


# ── CREATE ─────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_user(data: UserCreate, bg: BackgroundTasks, _=Depends(get_current_admin)):
    uid = data.user_id or next_user_id()
    now = datetime.utcnow()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO USERS (user_id,username,gender,phone,email,birth_date,city,
              register_ip,user_status,is_test,app_version,reg_version,reg_source,
              reg_channel,package_id,mark,tag,create_time,update_time)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17,:18,:19)
        """, [uid, data.username, data.gender, data.phone, data.email, data.birth_date,
              data.city, data.register_ip, data.user_status, data.is_test,
              data.app_version, data.reg_version, data.reg_source, data.reg_channel,
              data.package_id, data.mark, data.tag, now, now])

        cur.execute("""
            INSERT INTO USER_FINANCIALS (user_id,balance,user_balance,total_deposits,
              total_withdrawals,frozen_amount,withdraw_limit,recharge_count)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8)
        """, [uid, data.balance, data.user_balance, data.total_deposits,
              data.total_withdrawals, data.frozen_amount, data.withdraw_limit, data.recharge_count])

        cur.execute("""
            INSERT INTO USER_AGENTS (user_id,agent_status,agent_user_id,parent_user_id,
              direct_parent,agent_level1,agent_level2,agent_level3,agent_level4,
              agent_level,inviter_user_id,member_level)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12)
        """, [uid, data.agent_status, data.agent_user_id, data.parent_user_id,
              data.direct_parent, data.agent_level1, data.agent_level2, data.agent_level3,
              data.agent_level4, data.agent_level, data.inviter_user_id, data.member_level])

        cur.execute("""
            INSERT INTO USER_DEVICES (user_id,register_device,login_device,
              last_login_device,device_id,push_token,last_active_time)
            VALUES (:1,:2,:3,:4,:5,:6,:7)
        """, [uid, data.register_device, data.login_device, data.last_login_device,
              data.device_id, data.push_token, data.last_active_time])

        cur.execute("""
            INSERT INTO USER_IM (user_id,im_user_id,im_user_status,im_customer,group_name,adjust_adid)
            VALUES (:1,:2,:3,:4,:5,:6)
        """, [uid, data.im_user_id, data.im_user_status, data.im_customer,
              data.group_name, data.adjust_adid])

        cur.execute("""
            INSERT INTO USER_FOLLOWUP (user_id,flow_up_time,next_flow_up_time)
            VALUES (:1,:2,:3)
        """, [uid, data.flow_up_time, data.next_flow_up_time])

        conn.commit()
    finally:
        conn.close()

    bg.add_task(regenerate_excel)
    return {"user_id": uid, "message": "User created successfully"}


# ── UPDATE ─────────────────────────────────────────────────

@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, bg: BackgroundTasks, _=Depends(get_current_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Check exists
        cur.execute("SELECT 1 FROM USERS WHERE user_id = :1", [user_id])
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        now = datetime.utcnow()

        cur.execute("""
            UPDATE USERS SET
              username=:1, gender=:2, phone=:3, email=:4, birth_date=:5, city=:6,
              register_ip=:7, user_status=:8, is_test=:9, app_version=:10,
              reg_version=:11, reg_source=:12, reg_channel=:13, package_id=:14,
              mark=:15, tag=:16, update_time=:17
            WHERE user_id=:18
        """, [data.username, data.gender, data.phone, data.email, data.birth_date,
              data.city, data.register_ip, data.user_status, data.is_test,
              data.app_version, data.reg_version, data.reg_source, data.reg_channel,
              data.package_id, data.mark, data.tag, now, user_id])

        cur.execute("""
            UPDATE USER_FINANCIALS SET
              balance=:1, user_balance=:2, total_deposits=:3, total_withdrawals=:4,
              frozen_amount=:5, withdraw_limit=:6, recharge_count=:7
            WHERE user_id=:8
        """, [data.balance, data.user_balance, data.total_deposits, data.total_withdrawals,
              data.frozen_amount, data.withdraw_limit, data.recharge_count, user_id])

        cur.execute("""
            UPDATE USER_AGENTS SET
              agent_status=:1, agent_user_id=:2, parent_user_id=:3, direct_parent=:4,
              agent_level1=:5, agent_level2=:6, agent_level3=:7, agent_level4=:8,
              agent_level=:9, inviter_user_id=:10, member_level=:11
            WHERE user_id=:12
        """, [data.agent_status, data.agent_user_id, data.parent_user_id, data.direct_parent,
              data.agent_level1, data.agent_level2, data.agent_level3, data.agent_level4,
              data.agent_level, data.inviter_user_id, data.member_level, user_id])

        cur.execute("""
            UPDATE USER_DEVICES SET
              register_device=:1, login_device=:2, last_login_device=:3,
              device_id=:4, push_token=:5, last_active_time=:6
            WHERE user_id=:7
        """, [data.register_device, data.login_device, data.last_login_device,
              data.device_id, data.push_token, data.last_active_time, user_id])

        cur.execute("""
            UPDATE USER_IM SET
              im_user_id=:1, im_user_status=:2, im_customer=:3, group_name=:4, adjust_adid=:5
            WHERE user_id=:6
        """, [data.im_user_id, data.im_user_status, data.im_customer,
              data.group_name, data.adjust_adid, user_id])

        cur.execute("""
            UPDATE USER_FOLLOWUP SET flow_up_time=:1, next_flow_up_time=:2
            WHERE user_id=:3
        """, [data.flow_up_time, data.next_flow_up_time, user_id])

        conn.commit()
    finally:
        conn.close()

    bg.add_task(regenerate_excel)
    return {"message": "User updated successfully"}


# ── DELETE ─────────────────────────────────────────────────

@router.delete("/{user_id}")
def delete_user(user_id: int, bg: BackgroundTasks, _=Depends(get_current_admin)):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM USERS WHERE user_id = :1", [user_id])
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        # Delete child tables first (FK constraints)
        for table in ["USER_FOLLOWUP", "USER_IM", "USER_DEVICES", "USER_AGENTS", "USER_FINANCIALS"]:
            cur.execute(f"DELETE FROM {table} WHERE user_id = :1", [user_id])
        cur.execute("DELETE FROM USERS WHERE user_id = :1", [user_id])
        conn.commit()
    finally:
        conn.close()

    bg.add_task(regenerate_excel)
    return {"message": "User deleted successfully"}


# ── REFERRALS ──────────────────────────────────────────────

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
