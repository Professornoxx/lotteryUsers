"""
Import Excel data into Oracle Database.
Usage: python import_excel.py --file path/to/file.xlsx
"""
import argparse
import oracledb
import pandas as pd
from datetime import datetime
from app.core.config import settings

BATCH_SIZE = 500


def get_conn():
    return oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=f"{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE}",
    )


def safe_str(val, max_len=None):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if max_len:
        s = s[:max_len]
    return s or None


def safe_num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except Exception:
        return None


def safe_ts(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val
    try:
        return pd.to_datetime(val)
    except Exception:
        return None


def import_data(filepath: str):
    print(f"Reading {filepath}...")
    df = pd.read_excel(filepath, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    total = len(df)
    print(f"Total rows: {total}")

    conn = get_conn()
    cur = conn.cursor()

    users, financials, agents, devices, ims, followups = [], [], [], [], [], []

    for _, row in df.iterrows():
        uid = safe_num(row.iloc[0])
        if uid is None:
            continue
        uid = int(uid)

        users.append((
            uid,
            safe_str(row.iloc[10], 100),   # username
            safe_num(row.iloc[11]),          # gender
            safe_str(row.iloc[12], 20),      # phone
            safe_str(row.iloc[13], 200),     # email
            safe_ts(row.iloc[15]),           # birth_date
            safe_str(row.iloc[43], 100),     # city
            safe_str(row.iloc[14], 50),      # register_ip
            safe_num(row.iloc[26]),          # user_status
            safe_num(row.iloc[20]),          # is_test
            safe_str(row.iloc[16], 50),      # app_version
            safe_str(row.iloc[29], 50),      # reg_version
            safe_str(row.iloc[22], 50),      # reg_source
            safe_str(row.iloc[19], 100),     # reg_channel
            safe_num(row.iloc[55]),          # package_id
            safe_str(row.iloc[44], 500),     # mark
            safe_str(row.iloc[47], 200),     # tag
            safe_ts(row.iloc[53]),           # create_time
            safe_ts(row.iloc[54]),           # update_time
        ))

        financials.append((
            uid,
            safe_num(row.iloc[31]) or 0,    # balance
            safe_num(row.iloc[38]) or 0,    # user_balance
            safe_num(row.iloc[39]) or 0,    # total_deposits
            safe_num(row.iloc[41]) or 0,    # total_withdrawals
            safe_num(row.iloc[40]) or 0,    # frozen_amount
            safe_num(row.iloc[42]) or 0,    # withdraw_limit
            safe_num(row.iloc[32]) or 0,    # recharge_count
        ))

        agents.append((
            uid,
            safe_num(row.iloc[1]),           # agent_status
            safe_num(row.iloc[2]),           # agent_user_id
            safe_num(row.iloc[3]),           # parent_user_id
            safe_num(row.iloc[4]),           # direct_parent
            safe_num(row.iloc[5]),           # agent_level1
            safe_num(row.iloc[6]),           # agent_level2
            safe_num(row.iloc[7]),           # agent_level3
            safe_num(row.iloc[8]),           # agent_level4
            safe_num(row.iloc[9]),           # agent_level
            safe_num(row.iloc[21]),          # inviter_user_id
            safe_num(row.iloc[28]) or 0,    # member_level
        ))

        devices.append((
            uid,
            safe_str(row.iloc[17], 200),     # register_device
            safe_str(row.iloc[18], 200),     # login_device
            safe_str(row.iloc[24], 200),     # last_login_device
            safe_str(row.iloc[25], 200),     # device_id
            safe_str(row.iloc[27], 500),     # push_token
            safe_ts(row.iloc[23]),           # last_active_time
        ))

        ims.append((
            uid,
            safe_str(row.iloc[48], 100),     # im_user_id
            safe_str(row.iloc[49], 10),      # im_user_status
            safe_str(row.iloc[52], 100),     # im_customer
            safe_str(row.iloc[50], 100),     # group_name
            safe_str(row.iloc[51], 200),     # adjust_adid
        ))

        followups.append((
            uid,
            safe_ts(row.iloc[45]),           # flow_up_time
            safe_ts(row.iloc[46]),           # next_flow_up_time
        ))

    def batch_insert(sql, data, label):
        print(f"Inserting {len(data)} rows into {label}...")
        for i in range(0, len(data), BATCH_SIZE):
            cur.executemany(sql, data[i:i+BATCH_SIZE])
            conn.commit()
            print(f"  {label}: {min(i+BATCH_SIZE, len(data))}/{len(data)}")

    batch_insert(
        """INSERT INTO USERS (user_id,username,gender,phone,email,birth_date,city,
           register_ip,user_status,is_test,app_version,reg_version,reg_source,
           reg_channel,package_id,mark,tag,create_time,update_time)
           VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17,:18,:19)""",
        users, "USERS"
    )
    batch_insert(
        """INSERT INTO USER_FINANCIALS (user_id,balance,user_balance,total_deposits,
           total_withdrawals,frozen_amount,withdraw_limit,recharge_count)
           VALUES (:1,:2,:3,:4,:5,:6,:7,:8)""",
        financials, "USER_FINANCIALS"
    )
    batch_insert(
        """INSERT INTO USER_AGENTS (user_id,agent_status,agent_user_id,parent_user_id,
           direct_parent,agent_level1,agent_level2,agent_level3,agent_level4,
           agent_level,inviter_user_id,member_level)
           VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12)""",
        agents, "USER_AGENTS"
    )
    batch_insert(
        """INSERT INTO USER_DEVICES (user_id,register_device,login_device,
           last_login_device,device_id,push_token,last_active_time)
           VALUES (:1,:2,:3,:4,:5,:6,:7)""",
        devices, "USER_DEVICES"
    )
    batch_insert(
        """INSERT INTO USER_IM (user_id,im_user_id,im_user_status,im_customer,
           group_name,adjust_adid)
           VALUES (:1,:2,:3,:4,:5,:6)""",
        ims, "USER_IM"
    )
    batch_insert(
        """INSERT INTO USER_FOLLOWUP (user_id,flow_up_time,next_flow_up_time)
           VALUES (:1,:2,:3)""",
        followups, "USER_FOLLOWUP"
    )

    cur.close()
    conn.close()
    print(f"\nDone! {total} users imported successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to Excel file")
    args = parser.parse_args()
    import_data(args.file)
