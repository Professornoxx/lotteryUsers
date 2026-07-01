"""
Fetches deposit, withdrawal, and wallet data from external APIs
and upserts into Supabase every 20 minutes.
New users found in any API response are automatically saved to users table.
"""
import requests
from datetime import datetime
from app.core.database import query_one
from sqlalchemy import text

PACKAGE_ID = 10
APIS = {
    "deposits":    "https://api.rumanagers.online/prod-api/business/water/export",
    "withdrawals": "https://api.rumanagers.online/prod-api/business/withdraw/export",
    "wallet":      "https://api.rumanagers.online/prod-api/business/detail/export",
}


def get_token(db):
    row = query_one(db, "SELECT bearer_token FROM pipeline_config WHERE id=1", {})
    return row["bearer_token"] if row else None


def save_status(db, status: str):
    db.execute(text(
        "UPDATE pipeline_config SET last_sync=:t, last_status=:s WHERE id=1"
    ), {"t": datetime.utcnow(), "s": status})
    db.commit()


def fetch_api(url: str, token: str):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json={"packageId": PACKAGE_ID}, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"{resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if isinstance(data, list):
        return data
    for key in ("data", "rows", "list", "records", "result"):
        if key in data and isinstance(data[key], list):
            return data[key]
    return []


def ts(val):
    if not val:
        return None
    try:
        import pandas as pd
        r = pd.to_datetime(val, errors="coerce")
        return None if str(r) == "NaT" else r.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return None


def safe(val, max_len=None):
    if val is None:
        return None
    s = str(val).strip()
    if s in ("None", "nan", ""):
        return None
    return s[:max_len] if max_len else s


def upsert_users_from_rows(db, rows):
    """Extract user info from any API row and upsert into users table."""
    users = []
    fins = []
    for r in rows:
        uid = r.get("userId") or r.get("user_id") or r.get("uid")
        if not uid:
            continue
        try:
            uid = int(uid)
        except:
            continue
        users.append({
            "user_id": uid,
            "username": safe(r.get("username") or r.get("nickName"), 100),
            "phone": safe(r.get("phone") or r.get("mobile"), 20),
            "city": safe(r.get("city") or r.get("area"), 100),
            "reg_channel": safe(r.get("channel") or r.get("regChannel"), 100),
            "reg_source": safe(r.get("source") or r.get("regSource"), 50),
            "user_status": int(r.get("status") or 0) if str(r.get("status", "")).isdigit() else 0,
            "update_time": ts(r.get("updateTime") or r.get("update_time")),
        })
        balance = r.get("balance") or r.get("userBalance") or 0
        deposits = r.get("totalDeposit") or r.get("totalRecharge") or r.get("rechargeAmount") or 0
        withdrawals = r.get("totalWithdraw") or r.get("totalWithdrawal") or r.get("withdrawAmount") or 0
        if any([balance, deposits, withdrawals]):
            fins.append({
                "user_id": uid,
                "balance": float(balance),
                "total_deposits": float(deposits),
                "total_withdrawals": float(withdrawals),
            })

    if users:
        db.execute(text("""
            INSERT INTO users (user_id, username, phone, city, reg_channel, reg_source, user_status, update_time)
            VALUES (:user_id, :username, :phone, :city, :reg_channel, :reg_source, :user_status, :update_time)
            ON CONFLICT (user_id) DO UPDATE SET
              username = COALESCE(EXCLUDED.username, users.username),
              phone    = COALESCE(EXCLUDED.phone, users.phone),
              city     = COALESCE(EXCLUDED.city, users.city),
              update_time = EXCLUDED.update_time
        """), users)

    if fins:
        db.execute(text("""
            INSERT INTO user_financials (user_id, balance, total_deposits, total_withdrawals)
            VALUES (:user_id, :balance, :total_deposits, :total_withdrawals)
            ON CONFLICT (user_id) DO UPDATE SET
              balance           = EXCLUDED.balance,
              total_deposits    = EXCLUDED.total_deposits,
              total_withdrawals = EXCLUDED.total_withdrawals
        """), fins)

    db.commit()
    return len(users)


def sync_all(db):
    token = get_token(db)
    if not token:
        raise Exception("No bearer token configured")

    results = {}
    total_new_users = 0

    # --- DEPOSITS ---
    try:
        rows = fetch_api(APIS["deposits"], token)
        if rows:
            # Save users found in deposit data
            total_new_users += upsert_users_from_rows(db, rows)
            # Save deposit records
            records = []
            for r in rows:
                uid = r.get("userId") or r.get("user_id") or r.get("uid")
                amt = r.get("amount") or r.get("rechargeAmount") or r.get("money") or 0
                ct = ts(r.get("createTime") or r.get("create_time"))
                if not uid or not ct:
                    continue
                records.append({
                    "user_id": int(uid), "amount": float(amt),
                    "username": safe(r.get("username") or r.get("nickName"), 100),
                    "phone": safe(r.get("phone") or r.get("mobile"), 20),
                    "status": safe(r.get("status") or r.get("state"), 50),
                    "channel": safe(r.get("channel") or r.get("payChannel"), 100),
                    "create_time": ct,
                    "update_time": ts(r.get("updateTime") or r.get("update_time")),
                })
            if records:
                db.execute(text("""
                    INSERT INTO deposits (user_id,username,phone,amount,status,channel,create_time,update_time)
                    VALUES (:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                    ON CONFLICT (user_id, create_time) DO UPDATE SET
                      amount=EXCLUDED.amount, status=EXCLUDED.status, update_time=EXCLUDED.update_time
                """), records)
                db.commit()
        results["deposits"] = f"{len(rows)} synced"
    except Exception as e:
        results["deposits"] = f"Error: {e}"

    # --- WITHDRAWALS ---
    try:
        rows = fetch_api(APIS["withdrawals"], token)
        if rows:
            total_new_users += upsert_users_from_rows(db, rows)
            records = []
            for r in rows:
                uid = r.get("userId") or r.get("user_id") or r.get("uid")
                amt = r.get("amount") or r.get("withdrawAmount") or r.get("money") or 0
                ct = ts(r.get("createTime") or r.get("create_time"))
                if not uid or not ct:
                    continue
                records.append({
                    "user_id": int(uid), "amount": float(amt),
                    "username": safe(r.get("username") or r.get("nickName"), 100),
                    "phone": safe(r.get("phone") or r.get("mobile"), 20),
                    "status": safe(r.get("status") or r.get("state"), 50),
                    "channel": safe(r.get("channel") or r.get("payChannel"), 100),
                    "create_time": ct,
                    "update_time": ts(r.get("updateTime") or r.get("update_time")),
                })
            if records:
                db.execute(text("""
                    INSERT INTO withdrawals (user_id,username,phone,amount,status,channel,create_time,update_time)
                    VALUES (:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                    ON CONFLICT (user_id, create_time) DO UPDATE SET
                      amount=EXCLUDED.amount, status=EXCLUDED.status, update_time=EXCLUDED.update_time
                """), records)
                db.commit()
        results["withdrawals"] = f"{len(rows)} synced"
    except Exception as e:
        results["withdrawals"] = f"Error: {e}"

    # --- WALLET DETAILS (most complete user data) ---
    try:
        rows = fetch_api(APIS["wallet"], token)
        if rows:
            total_new_users += upsert_users_from_rows(db, rows)
            records = []
            for r in rows:
                uid = r.get("userId") or r.get("user_id") or r.get("uid")
                if not uid:
                    continue
                records.append({
                    "user_id": int(uid),
                    "username": safe(r.get("username") or r.get("nickName"), 100),
                    "phone": safe(r.get("phone") or r.get("mobile"), 20),
                    "balance": float(r.get("balance") or r.get("userBalance") or 0),
                    "total_deposits": float(r.get("totalDeposit") or r.get("totalRecharge") or 0),
                    "total_withdrawals": float(r.get("totalWithdraw") or r.get("totalWithdrawal") or 0),
                    "update_time": ts(r.get("updateTime") or r.get("update_time")),
                })
            if records:
                db.execute(text("""
                    INSERT INTO wallet_details (user_id,username,phone,balance,total_deposits,total_withdrawals,update_time)
                    VALUES (:user_id,:username,:phone,:balance,:total_deposits,:total_withdrawals,:update_time)
                    ON CONFLICT (user_id) DO UPDATE SET
                      balance=EXCLUDED.balance, total_deposits=EXCLUDED.total_deposits,
                      total_withdrawals=EXCLUDED.total_withdrawals, update_time=EXCLUDED.update_time
                """), records)
                db.commit()
        results["wallet"] = f"{len(rows)} synced"
    except Exception as e:
        results["wallet"] = f"Error: {e}"

    results["users_updated"] = total_new_users
    status = " | ".join(f"{k}: {v}" for k, v in results.items())
    save_status(db, status)
    return results
