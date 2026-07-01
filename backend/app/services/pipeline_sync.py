"""
Fetches deposit, withdrawal, and wallet data from external APIs
and upserts into Supabase. Called on token save + every 20 minutes.
"""
import requests
from datetime import datetime
from app.core.database import query_one, query
from sqlalchemy import text

PACKAGE_ID = 10
APIS = {
    "deposits":  "https://api.rumanagers.online/prod-api/business/water/export",
    "withdrawals": "https://api.rumanagers.online/prod-api/business/withdraw/export",
    "wallet":    "https://api.rumanagers.online/prod-api/business/detail/export",
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
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json={"packageId": PACKAGE_ID}, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"API {url} returned {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    # Handle common response wrappers
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
        return str(pd_parse(val))[:19].replace("T", " ")
    except:
        return None


def pd_parse(val):
    import pandas as pd
    r = pd.to_datetime(val, errors="coerce")
    return None if str(r) == "NaT" else r


def sync_all(db):
    token = get_token(db)
    if not token:
        raise Exception("No bearer token configured")

    results = {}

    # --- DEPOSITS ---
    try:
        rows = fetch_api(APIS["deposits"], token)
        if rows:
            records = []
            for r in rows:
                uid = r.get("userId") or r.get("user_id") or r.get("uid")
                amt = r.get("amount") or r.get("rechargeAmount") or r.get("money") or 0
                records.append({
                    "user_id": int(uid) if uid else None,
                    "username": str(r.get("username") or r.get("nickName") or "")[:100],
                    "phone": str(r.get("phone") or r.get("mobile") or "")[:20],
                    "amount": float(amt),
                    "status": str(r.get("status") or r.get("state") or "")[:50],
                    "channel": str(r.get("channel") or r.get("payChannel") or "")[:100],
                    "create_time": ts(r.get("createTime") or r.get("create_time")),
                    "update_time": ts(r.get("updateTime") or r.get("update_time")),
                })
            records = [x for x in records if x["user_id"]]
            if records:
                db.execute(text("""
                    INSERT INTO deposits (user_id,username,phone,amount,status,channel,create_time,update_time)
                    VALUES (:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                    ON CONFLICT (user_id, create_time) DO UPDATE SET
                      amount=EXCLUDED.amount, status=EXCLUDED.status, update_time=EXCLUDED.update_time
                """), records)
                db.commit()
        results["deposits"] = f"{len(rows)} rows synced"
    except Exception as e:
        results["deposits"] = f"Error: {e}"

    # --- WITHDRAWALS ---
    try:
        rows = fetch_api(APIS["withdrawals"], token)
        if rows:
            records = []
            for r in rows:
                uid = r.get("userId") or r.get("user_id") or r.get("uid")
                amt = r.get("amount") or r.get("withdrawAmount") or r.get("money") or 0
                records.append({
                    "user_id": int(uid) if uid else None,
                    "username": str(r.get("username") or r.get("nickName") or "")[:100],
                    "phone": str(r.get("phone") or r.get("mobile") or "")[:20],
                    "amount": float(amt),
                    "status": str(r.get("status") or r.get("state") or "")[:50],
                    "channel": str(r.get("channel") or r.get("payChannel") or "")[:100],
                    "create_time": ts(r.get("createTime") or r.get("create_time")),
                    "update_time": ts(r.get("updateTime") or r.get("update_time")),
                })
            records = [x for x in records if x["user_id"]]
            if records:
                db.execute(text("""
                    INSERT INTO withdrawals (user_id,username,phone,amount,status,channel,create_time,update_time)
                    VALUES (:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                    ON CONFLICT (user_id, create_time) DO UPDATE SET
                      amount=EXCLUDED.amount, status=EXCLUDED.status, update_time=EXCLUDED.update_time
                """), records)
                db.commit()
        results["withdrawals"] = f"{len(rows)} rows synced"
    except Exception as e:
        results["withdrawals"] = f"Error: {e}"

    # --- WALLET DETAILS ---
    try:
        rows = fetch_api(APIS["wallet"], token)
        if rows:
            records = []
            for r in rows:
                uid = r.get("userId") or r.get("user_id") or r.get("uid")
                records.append({
                    "user_id": int(uid) if uid else None,
                    "username": str(r.get("username") or r.get("nickName") or "")[:100],
                    "phone": str(r.get("phone") or r.get("mobile") or "")[:20],
                    "balance": float(r.get("balance") or r.get("userBalance") or 0),
                    "total_deposits": float(r.get("totalDeposit") or r.get("totalRecharge") or 0),
                    "total_withdrawals": float(r.get("totalWithdraw") or r.get("totalWithdrawal") or 0),
                    "update_time": ts(r.get("updateTime") or r.get("update_time")),
                })
            records = [x for x in records if x["user_id"]]
            if records:
                db.execute(text("""
                    INSERT INTO wallet_details (user_id,username,phone,balance,total_deposits,total_withdrawals,update_time)
                    VALUES (:user_id,:username,:phone,:balance,:total_deposits,:total_withdrawals,:update_time)
                    ON CONFLICT (user_id) DO UPDATE SET
                      balance=EXCLUDED.balance, total_deposits=EXCLUDED.total_deposits,
                      total_withdrawals=EXCLUDED.total_withdrawals, update_time=EXCLUDED.update_time
                """), records)
                db.commit()
        results["wallet"] = f"{len(rows)} rows synced"
    except Exception as e:
        results["wallet"] = f"Error: {e}"

    status = " | ".join(f"{k}: {v}" for k, v in results.items())
    save_status(db, status)
    return results
