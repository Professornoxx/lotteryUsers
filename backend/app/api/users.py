from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.api.auth import get_current_admin
from app.schemas.user import UserCreate, UserUpdate
from app.services.excel_sync import regenerate_excel
from datetime import datetime

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
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    where = ["1=1"]
    params = {}

    if search:
        where.append("(u.username ILIKE :search OR u.phone ILIKE :search)")
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

    total = db.execute(text(f"""
        SELECT COUNT(*) FROM users u
        LEFT JOIN user_financials f ON f.user_id = u.user_id
        LEFT JOIN user_agents ua ON ua.user_id = u.user_id
        WHERE {where_sql}
    """), params).scalar()

    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    result = db.execute(text(f"""
        SELECT u.user_id, u.username, u.phone, u.email, u.city,
               u.gender, u.user_status, u.is_test, u.reg_channel,
               u.reg_source, u.create_time,
               f.balance, f.total_deposits, f.total_withdrawals,
               f.frozen_amount, f.recharge_count,
               ua.agent_status, ua.agent_level, ua.member_level,
               d.last_active_time
        FROM users u
        LEFT JOIN user_financials f ON f.user_id = u.user_id
        LEFT JOIN user_agents ua ON ua.user_id = u.user_id
        LEFT JOIN user_devices d ON d.user_id = u.user_id
        WHERE {where_sql}
        ORDER BY u.create_time DESC
        LIMIT :limit OFFSET :offset
    """), params)

    cols = list(result.keys())
    rows = [dict(zip(cols, r)) for r in result.fetchall()]
    return {"page": page, "page_size": page_size, "total": total, "data": rows}


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    result = db.execute(text("""
        SELECT u.*, f.balance, f.user_balance, f.total_deposits,
               f.total_withdrawals, f.frozen_amount, f.withdraw_limit, f.recharge_count,
               ua.agent_status, ua.agent_level, ua.member_level,
               ua.parent_user_id, ua.inviter_user_id,
               ua.agent_level1, ua.agent_level2, ua.agent_level3, ua.agent_level4,
               d.register_device, d.login_device, d.last_login_device,
               d.device_id, d.push_token, d.last_active_time,
               i.im_user_id, i.im_user_status, i.im_customer, i.group_name, i.adjust_adid,
               fu.flow_up_time, fu.next_flow_up_time
        FROM users u
        LEFT JOIN user_financials f  ON f.user_id  = u.user_id
        LEFT JOIN user_agents ua     ON ua.user_id = u.user_id
        LEFT JOIN user_devices d     ON d.user_id  = u.user_id
        LEFT JOIN user_im i          ON i.user_id  = u.user_id
        LEFT JOIN user_followup fu   ON fu.user_id = u.user_id
        WHERE u.user_id = :uid
    """), {"uid": user_id})
    cols = list(result.keys())
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(zip(cols, row))


@router.post("/", status_code=201)
def create_user(data: UserCreate, bg: BackgroundTasks, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    if data.user_id:
        uid = data.user_id
    else:
        uid = db.execute(text("SELECT COALESCE(MAX(user_id), 100000) + 1 FROM users")).scalar()

    now = datetime.utcnow()
    db.execute(text("""
        INSERT INTO users (user_id,username,gender,phone,email,birth_date,city,
          register_ip,user_status,is_test,app_version,reg_version,reg_source,
          reg_channel,package_id,mark,tag,create_time,update_time)
        VALUES (:user_id,:username,:gender,:phone,:email,:birth_date,:city,
          :register_ip,:user_status,:is_test,:app_version,:reg_version,:reg_source,
          :reg_channel,:package_id,:mark,:tag,:now,:now)
    """), {**data.model_dump(), "user_id": uid, "now": now})

    db.execute(text("""
        INSERT INTO user_financials (user_id,balance,user_balance,total_deposits,
          total_withdrawals,frozen_amount,withdraw_limit,recharge_count)
        VALUES (:user_id,:balance,:user_balance,:total_deposits,
          :total_withdrawals,:frozen_amount,:withdraw_limit,:recharge_count)
    """), {**data.model_dump(), "user_id": uid})

    db.execute(text("""
        INSERT INTO user_agents (user_id,agent_status,agent_user_id,parent_user_id,
          direct_parent,agent_level1,agent_level2,agent_level3,agent_level4,
          agent_level,inviter_user_id,member_level)
        VALUES (:user_id,:agent_status,:agent_user_id,:parent_user_id,
          :direct_parent,:agent_level1,:agent_level2,:agent_level3,:agent_level4,
          :agent_level,:inviter_user_id,:member_level)
    """), {**data.model_dump(), "user_id": uid})

    db.execute(text("""
        INSERT INTO user_devices (user_id,register_device,login_device,
          last_login_device,device_id,push_token,last_active_time)
        VALUES (:user_id,:register_device,:login_device,:last_login_device,
          :device_id,:push_token,:last_active_time)
    """), {**data.model_dump(), "user_id": uid})

    db.execute(text("""
        INSERT INTO user_im (user_id,im_user_id,im_user_status,im_customer,group_name,adjust_adid)
        VALUES (:user_id,:im_user_id,:im_user_status,:im_customer,:group_name,:adjust_adid)
    """), {**data.model_dump(), "user_id": uid})

    db.execute(text("""
        INSERT INTO user_followup (user_id,flow_up_time,next_flow_up_time)
        VALUES (:user_id,:flow_up_time,:next_flow_up_time)
    """), {**data.model_dump(), "user_id": uid})

    db.commit()
    bg.add_task(regenerate_excel)
    return {"user_id": uid, "message": "User created successfully"}


@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, bg: BackgroundTasks, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    existing = db.execute(text("SELECT 1 FROM users WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    p = {**data.model_dump(), "user_id": user_id, "now": now}

    db.execute(text("""
        UPDATE users SET username=:username, gender=:gender, phone=:phone, email=:email,
          birth_date=:birth_date, city=:city, register_ip=:register_ip,
          user_status=:user_status, is_test=:is_test, app_version=:app_version,
          reg_version=:reg_version, reg_source=:reg_source, reg_channel=:reg_channel,
          package_id=:package_id, mark=:mark, tag=:tag, update_time=:now
        WHERE user_id=:user_id
    """), p)

    db.execute(text("""
        UPDATE user_financials SET balance=:balance, user_balance=:user_balance,
          total_deposits=:total_deposits, total_withdrawals=:total_withdrawals,
          frozen_amount=:frozen_amount, withdraw_limit=:withdraw_limit,
          recharge_count=:recharge_count
        WHERE user_id=:user_id
    """), p)

    db.execute(text("""
        UPDATE user_agents SET agent_status=:agent_status, agent_user_id=:agent_user_id,
          parent_user_id=:parent_user_id, direct_parent=:direct_parent,
          agent_level1=:agent_level1, agent_level2=:agent_level2,
          agent_level3=:agent_level3, agent_level4=:agent_level4,
          agent_level=:agent_level, inviter_user_id=:inviter_user_id,
          member_level=:member_level
        WHERE user_id=:user_id
    """), p)

    db.execute(text("""
        UPDATE user_devices SET register_device=:register_device,
          login_device=:login_device, last_login_device=:last_login_device,
          device_id=:device_id, push_token=:push_token,
          last_active_time=:last_active_time
        WHERE user_id=:user_id
    """), p)

    db.execute(text("""
        UPDATE user_im SET im_user_id=:im_user_id, im_user_status=:im_user_status,
          im_customer=:im_customer, group_name=:group_name, adjust_adid=:adjust_adid
        WHERE user_id=:user_id
    """), p)

    db.execute(text("""
        UPDATE user_followup SET flow_up_time=:flow_up_time,
          next_flow_up_time=:next_flow_up_time
        WHERE user_id=:user_id
    """), p)

    db.commit()
    bg.add_task(regenerate_excel)
    return {"message": "User updated successfully"}


@router.delete("/{user_id}")
def delete_user(user_id: int, bg: BackgroundTasks, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    existing = db.execute(text("SELECT 1 FROM users WHERE user_id = :uid"), {"uid": user_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    db.execute(text("DELETE FROM users WHERE user_id = :uid"), {"uid": user_id})
    db.commit()
    bg.add_task(regenerate_excel)
    return {"message": "User deleted successfully"}


@router.get("/{user_id}/referrals")
def get_referrals(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    result = db.execute(text("""
        SELECT u.user_id, u.username, u.phone, u.city, u.create_time,
               f.total_deposits, f.balance
        FROM users u
        LEFT JOIN user_financials f ON f.user_id = u.user_id
        LEFT JOIN user_agents ua ON ua.user_id = u.user_id
        WHERE ua.inviter_user_id = :uid
        ORDER BY u.create_time DESC
    """), {"uid": user_id})
    cols = list(result.keys())
    return [dict(zip(cols, r)) for r in result.fetchall()]
