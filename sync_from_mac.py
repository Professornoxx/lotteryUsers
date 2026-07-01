#!/usr/bin/env python3
"""
Run this script from your Mac whenever you want to sync data from the APIs.
It fetches all 3 APIs (works because your Mac's IP is not blocked)
and writes directly to Supabase.

Usage:
  python3 sync_from_mac.py
  python3 sync_from_mac.py --token YOUR_NEW_TOKEN
  python3 sync_from_mac.py --date 2026-07-01
"""
import sys, argparse, requests, io, json, math
from datetime import datetime, date

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip3 install pandas openpyxl requests")
    sys.exit(1)

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("ERROR: sqlalchemy not installed. Run: pip3 install sqlalchemy psycopg2-binary")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.dglehhqpwdsyuezzupje:Brightpathtec%40%40@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
SUPABASE_URL  = "https://dglehhqpwdsyuezzupje.supabase.co"
SUPABASE_ANON = "sb_publishable_5ZBkIm5AYM-0D-KDVgOGpQ_xoQtx59o"

APIS = {
    "deposits":    "https://api.rumanagers.online/prod-api/business/water/export",
    "withdrawals": "https://api.rumanagers.online/prod-api/business/withdraw/export",
    "wallet":      "https://api.rumanagers.online/prod-api/business/detail/export",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def safe(val, max_len=None):
    if val is None: return None
    try:
        if isinstance(val, float) and math.isnan(val): return None
    except: pass
    s = str(val).strip()
    if s in ("None", "nan", "NaT", ""): return None
    return s[:max_len] if max_len else s or None

def num(val):
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)): return 0.0
        return float(val)
    except: return 0.0

def ts(val):
    if val is None: return None
    try:
        r = pd.to_datetime(val, errors="coerce")
        return None if str(r) == "NaT" else r.strftime("%Y-%m-%d %H:%M:%S")
    except: return None

def get_token_from_db(engine):
    with engine.connect() as conn:
        row = conn.execute(text("SELECT bearer_token FROM pipeline_config WHERE id=1")).fetchone()
        return row[0] if row else None

def save_status(engine, status):
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE pipeline_config SET last_sync=:t, last_status=:s WHERE id=1"
        ), {"t": datetime.utcnow(), "s": status})
    print(f"  ✓ Status saved: {status}")

def fetch_api(url, token, query_date):
    payload = {
        "packageId": 10, "pageNum": 1, "pageSize": 100000,
        "useUpiQuery": True, "queryDate": [query_date, query_date],
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    print(f"  → {resp.status_code}, {len(resp.content):,} bytes")
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")
    if resp.content[:2] == b"PK":
        df = pd.read_excel(io.BytesIO(resp.content), engine="openpyxl")
        return df
    raise Exception("Response was not an Excel file")

# ── Sync Functions ─────────────────────────────────────────────────────────
def sync_deposits(engine, df):
    records = []
    for _, r in df.iterrows():
        uid = r.get("UserId") or r.get("userId")
        ct = ts(r.get("createTime"))
        if uid is None or pd.isna(uid) or not ct: continue
        records.append({
            "user_id": int(uid),
            "username": safe(r.get("username") or r.get("nickName"), 100),
            "phone": safe(r.get("userPhone") or r.get("phone"), 20),
            "amount": num(r.get("RechargeAmount") or r.get("amount") or r.get("rechargeAmount")),
            "status": safe(r.get("status") or r.get("state"), 50),
            "channel": safe(r.get("channelName") or r.get("channel"), 100),
            "create_time": ct,
            "update_time": ts(r.get("updateTime")),
        })
    if records:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL statement_timeout=0"))
            conn.execute(text("""
                INSERT INTO deposits (user_id,username,phone,amount,status,channel,create_time,update_time)
                VALUES (:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                ON CONFLICT (user_id, create_time) DO UPDATE SET
                  amount=EXCLUDED.amount, status=EXCLUDED.status, update_time=EXCLUDED.update_time
            """), records)
        print(f"  ✓ Saved {len(records)} deposit records")
    return len(records)

def sync_withdrawals(engine, df):
    records = []
    for _, r in df.iterrows():
        uid = r.get("UserId") or r.get("userId")
        ct = ts(r.get("createTime"))
        if uid is None or pd.isna(uid) or not ct: continue
        records.append({
            "user_id": int(uid),
            "username": safe(r.get("username") or r.get("bankName"), 100),
            "phone": safe(r.get("userPhone") or r.get("phone"), 20),
            "amount": num(r.get("WithDrawAmount") or r.get("withdrawAmount") or r.get("amount")),
            "status": safe(r.get("0 Under review, 1 Payment processing, 2 Completed, 3 Rejected, 4 Failed") or r.get("status"), 50),
            "channel": safe(r.get("Withdraw Payment Channels") or r.get("channel"), 100),
            "create_time": ct,
            "update_time": ts(r.get("updateTime")),
        })
    if records:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL statement_timeout=0"))
            conn.execute(text("""
                INSERT INTO withdrawals (user_id,username,phone,amount,status,channel,create_time,update_time)
                VALUES (:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                ON CONFLICT (user_id, create_time) DO UPDATE SET
                  amount=EXCLUDED.amount, status=EXCLUDED.status, update_time=EXCLUDED.update_time
            """), records)
        print(f"  ✓ Saved {len(records)} withdrawal records")
    return len(records)

def sync_wallet(engine, df):
    records = []
    for _, r in df.iterrows():
        uid = r.get("UserId") or r.get("userId")
        if uid is None or pd.isna(uid): continue
        records.append({
            "user_id": int(uid),
            "username": safe(r.get("Game Name") or r.get("username"), 100),
            "phone": safe(r.get("userPhone") or r.get("phone"), 20),
            "balance": num(r.get("changeAfter") or r.get("balance")),
            "total_deposits": 0.0, "total_withdrawals": 0.0,
            "update_time": ts(r.get("updateTime")),
        })
    if records:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL statement_timeout=0"))
            conn.execute(text("""
                INSERT INTO wallet_details (user_id,username,phone,balance,total_deposits,total_withdrawals,update_time)
                VALUES (:user_id,:username,:phone,:balance,:total_deposits,:total_withdrawals,:update_time)
                ON CONFLICT (user_id) DO UPDATE SET
                  balance=EXCLUDED.balance, update_time=EXCLUDED.update_time
            """), records)
        print(f"  ✓ Saved {len(records)} wallet records")
    return len(records)

def upsert_users(engine, df, uid_key="UserId"):
    users = []
    for _, r in df.iterrows():
        uid = r.get(uid_key) or r.get("userId") or r.get("user_id")
        if uid is None or pd.isna(uid): continue
        users.append({
            "user_id": int(uid),
            "phone": safe(r.get("userPhone") or r.get("phone") or r.get("mobile"), 20),
            "username": safe(r.get("username") or r.get("nickName"), 100),
            "update_time": ts(r.get("updateTime") or r.get("update_time")),
        })
    if users:
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL statement_timeout=0"))
            conn.execute(text("""
                INSERT INTO users (user_id, phone, username, update_time)
                VALUES (:user_id, :phone, :username, :update_time)
                ON CONFLICT (user_id) DO UPDATE SET
                  phone = COALESCE(EXCLUDED.phone, users.phone),
                  username = COALESCE(EXCLUDED.username, users.username),
                  update_time = EXCLUDED.update_time
            """), users)
    return len(users)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="Bearer token (reads from DB if not specified)")
    parser.add_argument("--date", default=date.today().strftime("%Y-%m-%d"), help="Query date YYYY-MM-DD")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"  Lottery Sync from Mac — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Date: {args.date}")
    print(f"{'='*50}\n")

    engine = create_engine(DB_URL, connect_args={"connect_timeout": 30})

    token = args.token
    if not token:
        print("Reading token from database...")
        token = get_token_from_db(engine)
        if not token:
            print("ERROR: No token in database and none provided via --token flag")
            sys.exit(1)
        print(f"  ✓ Got token from DB ({len(token)} chars)")

    results = {}

    # Deposits
    print("\n[1/3] Fetching deposits...")
    try:
        df = fetch_api(APIS["deposits"], token, args.date)
        print(f"  Columns: {df.columns.tolist()[:6]}")
        upsert_users(engine, df)
        results["deposits"] = sync_deposits(engine, df)
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results["deposits"] = f"Error: {e}"

    # Withdrawals
    print("\n[2/3] Fetching withdrawals...")
    try:
        df = fetch_api(APIS["withdrawals"], token, args.date)
        print(f"  Columns: {df.columns.tolist()[:6]}")
        upsert_users(engine, df)
        results["withdrawals"] = sync_withdrawals(engine, df)
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results["withdrawals"] = f"Error: {e}"

    # Wallet
    print("\n[3/3] Fetching wallet...")
    try:
        df = fetch_api(APIS["wallet"], token, args.date)
        print(f"  Columns: {df.columns.tolist()[:6]}")
        upsert_users(engine, df)
        results["wallet"] = sync_wallet(engine, df)
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results["wallet"] = f"Error: {e}"

    # Save status
    status_parts = []
    for k, v in results.items():
        if isinstance(v, int):
            status_parts.append(f"{k}: {v} synced")
        else:
            status_parts.append(f"{k}: {v}")
    status_str = " | ".join(status_parts)
    save_status(engine, status_str)

    print(f"\n{'='*50}")
    print(f"  DONE: {status_str}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
