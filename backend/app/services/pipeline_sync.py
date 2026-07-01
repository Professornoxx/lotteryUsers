"""
Fetches deposit, withdrawal, and wallet data from external APIs
and upserts into Supabase every 20 minutes.
New users found in any API response are automatically saved to users table.
"""
import requests
import io
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


def build_payload():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return {
        "packageId": PACKAGE_ID,
        "pageNum": 1,
        "pageSize": 5000,
        "useUpiQuery": True,
        "queryDate": [today, today],
    }


def fetch_api(url: str, token: str):
    import pandas as pd
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=build_payload(), timeout=120)
    if resp.status_code != 200:
        raise Exception(f"{resp.status_code}: {resp.text[:200]}")

    # Excel binary response (starts with PK zip magic bytes)
    content_type = resp.headers.get("Content-Type", "")
    if resp.content[:2] == b"PK" or "octet-stream" in content_type or "spreadsheet" in content_type:
        try:
            df = pd.read_excel(io.BytesIO(resp.content), engine="openpyxl")
            return df.to_dict("records")
        except Exception as e:
            raise Exception(f"Excel parse error: {e}")

    if not resp.content or len(resp.content) < 2:
        return []

    try:
        data = resp.json()
        if isinstance(data, list):
            return data
        for key in ("data", "rows", "list", "records", "result"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return []
    except Exception:
        # Try Excel as fallback
        try:
            df = pd.read_excel(io.BytesIO(resp.content), engine="openpyxl")
            return df.to_dict("records")
        except Exception:
            return []


def safe(val, max_len=None):
    if val is None:
        return None
    import math
    try:
        if isinstance(val, float) and math.isnan(val):
            return None
    except Exception:
        pass
    s = str(val).strip()
    if s in ("None", "nan", "NaT", ""):
        return None
    return s[:max_len] if max_len else s or None


def num(val):
    if val is None:
        return 0.0
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return 0.0
        return float(val)
    except Exception:
        return 0.0


def ts(val):
    if val is None:
        return None
    try:
        import pandas as pd
        r = pd.to_datetime(val, errors="coerce")
        return None if str(r) == "NaT" else r.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def upsert_users_from_rows(db, rows, uid_key="UserId"):
    """Save any new users found in API rows into users table."""
    users = []
    for r in rows:
        uid = r.get(uid_key) or r.get("userId") or r.get("user_id")
        if not uid:
            continue
        try:
            uid = int(uid)
        except Exception:
            continue
        users.append({
            "user_id": uid,
            "phone": safe(r.get("userPhone") or r.get("phone") or r.get("mobile"), 20),
            "username": safe(r.get("username") or r.get("nickName"), 100),
            "update_time": ts(r.get("updateTime") or r.get("update_time")),
        })
    if users:
        db.execute(text("""
            INSERT INTO users (user_id, phone, username, update_time)
            VALUES (:user_id, :phone, :username, :update_time)
            ON CONFLICT (user_id) DO UPDATE SET
              phone = COALESCE(EXCLUDED.phone, users.phone),
              username = COALESCE(EXCLUDED.username, users.username),
              update_time = EXCLUDED.update_time
        """), users)
        db.commit()
    return len(users)


def sync_all(db):
    token = get_token(db)
    if not token:
        raise Exception("No bearer token configured")

    results = {}

    # --- DEPOSITS ---
    try:
        rows = fetch_api(APIS["deposits"], token)
        upsert_users_from_rows(db, rows)
        if rows:
            records = []
            for r in rows:
                uid = r.get("UserId") or r.get("userId") or r.get("user_id")
                ct = ts(r.get("createTime") or r.get("create_time"))
                if not uid or not ct:
                    continue
                records.append({
                    "user_id": int(uid),
                    "username": safe(r.get("username") or r.get("nickName"), 100),
                    "phone": safe(r.get("userPhone") or r.get("phone"), 20),
                    "amount": num(r.get("RechargeAmount") or r.get("amount") or r.get("rechargeAmount")),
                    "status": safe(r.get("status") or r.get("state"), 50),
                    "channel": safe(r.get("channelName") or r.get("channel") or r.get("Withdraw Payment Channels"), 100),
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
        upsert_users_from_rows(db, rows)
        if rows:
            records = []
            for r in rows:
                uid = r.get("UserId") or r.get("userId") or r.get("user_id")
                ct = ts(r.get("createTime") or r.get("create_time"))
                if not uid or not ct:
                    continue
                records.append({
                    "user_id": int(uid),
                    "username": safe(r.get("username") or r.get("bankName"), 100),
                    "phone": safe(r.get("userPhone") or r.get("phone"), 20),
                    "amount": num(r.get("WithDrawAmount") or r.get("withdrawAmount") or r.get("amount")),
                    "status": safe(r.get("0 Under review, 1 Payment processing, 2 Completed, 3 Rejected, 4 Failed") or r.get("status"), 50),
                    "channel": safe(r.get("Withdraw Payment Channels") or r.get("channel"), 100),
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

    # --- WALLET DETAILS ---
    try:
        rows = fetch_api(APIS["wallet"], token)
        upsert_users_from_rows(db, rows)
        if rows:
            records = []
            for r in rows:
                uid = r.get("UserId") or r.get("userId") or r.get("user_id")
                if not uid:
                    continue
                records.append({
                    "user_id": int(uid),
                    "username": safe(r.get("Game Name") or r.get("username"), 100),
                    "phone": safe(r.get("userPhone") or r.get("phone"), 20),
                    "balance": num(r.get("changeAfter") or r.get("balance")),
                    "total_deposits": 0.0,
                    "total_withdrawals": 0.0,
                    "update_time": ts(r.get("updateTime") or r.get("update_time")),
                })
            if records:
                db.execute(text("""
                    INSERT INTO wallet_details (user_id,username,phone,balance,total_deposits,total_withdrawals,update_time)
                    VALUES (:user_id,:username,:phone,:balance,:total_deposits,:total_withdrawals,:update_time)
                    ON CONFLICT (user_id) DO UPDATE SET
                      balance=EXCLUDED.balance, update_time=EXCLUDED.update_time
                """), records)
                db.commit()
        results["wallet"] = f"{len(rows)} synced"
    except Exception as e:
        results["wallet"] = f"Error: {e}"

    status = " | ".join(f"{k}: {v}" for k, v in results.items())
    save_status(db, status)
    return results
