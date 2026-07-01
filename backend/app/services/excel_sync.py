import os
import pandas as pd
from sqlalchemy import text
from app.core.database import SessionLocal

EXPORT_DIR = os.environ.get("EXPORT_DIR", os.path.join(os.path.dirname(__file__), "../../../exports"))


def get_export_path() -> str:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return os.path.join(EXPORT_DIR, "users_latest.xlsx")


def regenerate_excel() -> str:
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT u.user_id, u.username, u.gender, u.phone, u.email,
                   u.birth_date, u.city, u.register_ip, u.user_status, u.is_test,
                   u.app_version, u.reg_version, u.reg_source, u.reg_channel,
                   u.package_id, u.mark, u.tag, u.create_time, u.update_time,
                   f.balance, f.user_balance, f.total_deposits, f.total_withdrawals,
                   f.frozen_amount, f.withdraw_limit, f.recharge_count,
                   ua.agent_status, ua.agent_user_id, ua.parent_user_id,
                   ua.direct_parent, ua.agent_level1, ua.agent_level2,
                   ua.agent_level3, ua.agent_level4, ua.agent_level,
                   ua.inviter_user_id, ua.member_level,
                   d.register_device, d.login_device, d.last_login_device,
                   d.device_id, d.push_token, d.last_active_time,
                   i.im_user_id, i.im_user_status, i.im_customer,
                   i.group_name, i.adjust_adid,
                   fu.flow_up_time, fu.next_flow_up_time
            FROM users u
            LEFT JOIN user_financials f  ON f.user_id  = u.user_id
            LEFT JOIN user_agents ua     ON ua.user_id = u.user_id
            LEFT JOIN user_devices d     ON d.user_id  = u.user_id
            LEFT JOIN user_im i          ON i.user_id  = u.user_id
            LEFT JOIN user_followup fu   ON fu.user_id = u.user_id
            ORDER BY u.create_time DESC
        """))
        cols = list(result.keys())
        rows = result.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        path = get_export_path()
        df.to_excel(path, index=False, engine="openpyxl")
        return path
    finally:
        db.close()
