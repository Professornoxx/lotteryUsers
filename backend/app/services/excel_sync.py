"""
Auto-generates Excel file after every DB change.
Saves to /opt/lottery/exports/users_latest.xlsx (VM)
and keeps a copy at backend/exports/users_latest.xlsx (local dev).
"""
import os
import pandas as pd
from datetime import datetime
from app.core.database import get_connection

EXPORT_DIR = os.environ.get("EXPORT_DIR", os.path.join(os.path.dirname(__file__), "../../exports"))


def get_export_path() -> str:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return os.path.join(EXPORT_DIR, "users_latest.xlsx")


def regenerate_excel() -> str:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                u.user_id, u.username, u.gender, u.phone, u.email,
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
            FROM USERS u
            LEFT JOIN USER_FINANCIALS f  ON f.user_id  = u.user_id
            LEFT JOIN USER_AGENTS ua     ON ua.user_id = u.user_id
            LEFT JOIN USER_DEVICES d     ON d.user_id  = u.user_id
            LEFT JOIN USER_IM i          ON i.user_id  = u.user_id
            LEFT JOIN USER_FOLLOWUP fu   ON fu.user_id = u.user_id
            ORDER BY u.create_time DESC
        """)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        path = get_export_path()
        df.to_excel(path, index=False, engine="openpyxl")
        return path
    finally:
        conn.close()
