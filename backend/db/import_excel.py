"""
Import Excel data into Supabase / PostgreSQL.
Usage: python import_excel.py --file path/to/file.xlsx
"""
import argparse
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
BATCH = 500


def safe(val, max_len=None):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if max_len:
        s = s[:max_len]
    return s or None


def num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except Exception:
        return None


def ts(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val
    try:
        return pd.to_datetime(val).to_pydatetime()
    except Exception:
        return None


def import_data(filepath: str):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set in .env")

    engine = create_engine(db_url)
    print(f"Reading {filepath}...")
    df = pd.read_excel(filepath, sheet_name=0)
    total = len(df)
    print(f"Total rows: {total}")

    with engine.begin() as conn:
        for i in range(0, total, BATCH):
            batch = df.iloc[i:i+BATCH]
            users, fins, agents, devices, ims, followups = [], [], [], [], [], []

            for _, row in batch.iterrows():
                uid = num(row.iloc[0])
                if uid is None:
                    continue
                uid = int(uid)

                users.append({
                    "user_id": uid, "username": safe(row.iloc[10], 100),
                    "gender": num(row.iloc[11]), "phone": safe(row.iloc[12], 20),
                    "email": safe(row.iloc[13], 200), "birth_date": ts(row.iloc[15]),
                    "city": safe(row.iloc[43], 100), "register_ip": safe(row.iloc[14], 50),
                    "user_status": num(row.iloc[26]) or 0, "is_test": num(row.iloc[20]) or 0,
                    "app_version": safe(row.iloc[16], 50), "reg_version": safe(row.iloc[29], 50),
                    "reg_source": safe(row.iloc[22], 50), "reg_channel": safe(row.iloc[19], 100),
                    "package_id": num(row.iloc[55]), "mark": safe(row.iloc[44], 500),
                    "tag": safe(row.iloc[47], 200), "create_time": ts(row.iloc[53]),
                    "update_time": ts(row.iloc[54]),
                })
                fins.append({
                    "user_id": uid, "balance": num(row.iloc[31]) or 0,
                    "user_balance": num(row.iloc[38]) or 0, "total_deposits": num(row.iloc[39]) or 0,
                    "total_withdrawals": num(row.iloc[41]) or 0, "frozen_amount": num(row.iloc[40]) or 0,
                    "withdraw_limit": num(row.iloc[42]) or 0, "recharge_count": num(row.iloc[32]) or 0,
                })
                agents.append({
                    "user_id": uid, "agent_status": num(row.iloc[1]),
                    "agent_user_id": num(row.iloc[2]), "parent_user_id": num(row.iloc[3]),
                    "direct_parent": num(row.iloc[4]), "agent_level1": num(row.iloc[5]),
                    "agent_level2": num(row.iloc[6]), "agent_level3": num(row.iloc[7]),
                    "agent_level4": num(row.iloc[8]), "agent_level": num(row.iloc[9]),
                    "inviter_user_id": num(row.iloc[21]), "member_level": num(row.iloc[28]) or 0,
                })
                devices.append({
                    "user_id": uid, "register_device": safe(row.iloc[17], 200),
                    "login_device": safe(row.iloc[18], 200), "last_login_device": safe(row.iloc[24], 200),
                    "device_id": safe(row.iloc[25], 200), "push_token": safe(row.iloc[27], 500),
                    "last_active_time": ts(row.iloc[23]),
                })
                ims.append({
                    "user_id": uid, "im_user_id": safe(row.iloc[48], 100),
                    "im_user_status": safe(row.iloc[49], 10), "im_customer": safe(row.iloc[52], 100),
                    "group_name": safe(row.iloc[50], 100), "adjust_adid": safe(row.iloc[51], 200),
                })
                followups.append({
                    "user_id": uid, "flow_up_time": ts(row.iloc[45]),
                    "next_flow_up_time": ts(row.iloc[46]),
                })

            if users:
                conn.execute(text("""
                    INSERT INTO users (user_id,username,gender,phone,email,birth_date,city,
                      register_ip,user_status,is_test,app_version,reg_version,reg_source,
                      reg_channel,package_id,mark,tag,create_time,update_time)
                    VALUES (:user_id,:username,:gender,:phone,:email,:birth_date,:city,
                      :register_ip,:user_status,:is_test,:app_version,:reg_version,:reg_source,
                      :reg_channel,:package_id,:mark,:tag,:create_time,:update_time)
                    ON CONFLICT (user_id) DO NOTHING
                """), users)
                conn.execute(text("""
                    INSERT INTO user_financials (user_id,balance,user_balance,total_deposits,
                      total_withdrawals,frozen_amount,withdraw_limit,recharge_count)
                    VALUES (:user_id,:balance,:user_balance,:total_deposits,
                      :total_withdrawals,:frozen_amount,:withdraw_limit,:recharge_count)
                    ON CONFLICT (user_id) DO NOTHING
                """), fins)
                conn.execute(text("""
                    INSERT INTO user_agents (user_id,agent_status,agent_user_id,parent_user_id,
                      direct_parent,agent_level1,agent_level2,agent_level3,agent_level4,
                      agent_level,inviter_user_id,member_level)
                    VALUES (:user_id,:agent_status,:agent_user_id,:parent_user_id,
                      :direct_parent,:agent_level1,:agent_level2,:agent_level3,:agent_level4,
                      :agent_level,:inviter_user_id,:member_level)
                    ON CONFLICT (user_id) DO NOTHING
                """), agents)
                conn.execute(text("""
                    INSERT INTO user_devices (user_id,register_device,login_device,
                      last_login_device,device_id,push_token,last_active_time)
                    VALUES (:user_id,:register_device,:login_device,:last_login_device,
                      :device_id,:push_token,:last_active_time)
                    ON CONFLICT (user_id) DO NOTHING
                """), devices)
                conn.execute(text("""
                    INSERT INTO user_im (user_id,im_user_id,im_user_status,im_customer,
                      group_name,adjust_adid)
                    VALUES (:user_id,:im_user_id,:im_user_status,:im_customer,
                      :group_name,:adjust_adid)
                    ON CONFLICT (user_id) DO NOTHING
                """), ims)
                conn.execute(text("""
                    INSERT INTO user_followup (user_id,flow_up_time,next_flow_up_time)
                    VALUES (:user_id,:flow_up_time,:next_flow_up_time)
                    ON CONFLICT (user_id) DO NOTHING
                """), followups)

            print(f"  Imported {min(i+BATCH, total)}/{total} rows...")

    print(f"\nDone! {total} users imported successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    import_data(args.file)
