"""
GitHub Actions sync script — runs every 20 minutes via cron.
Reads DB_URL and BEARER_TOKEN from environment variables (GitHub Secrets).
"""
import os, io, math, requests, sys
from datetime import date
import pandas as pd
from sqlalchemy import create_engine, text

TOKEN  = os.environ["BEARER_TOKEN"]
TODAY  = date.today().strftime("%Y-%m-%d")

# Supabase REST API (avoids DB URL encoding issues)
SB_URL  = "https://dglehhqpwdsyuezzupje.supabase.co"
SB_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRnbGVoaHFwd2RzeXVlenp1cGplIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTM3MjI3OCwiZXhwIjoyMDY2OTQ4Mjc4fQ.dummy"
# Use direct DB URL with proper encoding
DB_URL = "postgresql://postgres.dglehhqpwdsyuezzupje:Brightpathtec%40%40@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

APIS = {
    "deposits":    "https://api.rumanagers.online/prod-api/business/water/export",
    "withdrawals": "https://api.rumanagers.online/prod-api/business/withdraw/export",
    "wallet":      "https://api.rumanagers.online/prod-api/business/detail/export",
}

PAYLOAD = {
    "packageId": 10, "pageNum": 1, "pageSize": 100000,
    "useUpiQuery": True, "queryDate": [TODAY, TODAY],
}
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

engine = create_engine(DB_URL, connect_args={"connect_timeout": 30})


def safe(val, n=None):
    if val is None: return None
    try:
        if isinstance(val, float) and math.isnan(val): return None
    except: pass
    s = str(val).strip()
    return None if s in ("None","nan","NaT","") else (s[:n] if n else s)

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

def fetch(url):
    r = requests.post(url, headers=HEADERS, json=PAYLOAD, timeout=180)
    print(f"  HTTP {r.status_code} — {len(r.content):,} bytes")
    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")
    if r.content[:2] != b"PK":
        print(f"  Response body: {r.content[:100]}")
        raise Exception(f"Response is not an Excel file ({len(r.content)} bytes)")
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")

def upsert_users(df):
    rows = []
    for _, r in df.iterrows():
        uid = r.get("UserId") or r.get("userId")
        if uid is None or pd.isna(uid): continue
        rows.append({"user_id": int(uid),
                     "phone": safe(r.get("userPhone") or r.get("phone"), 20),
                     "username": safe(r.get("username") or r.get("nickName"), 100),
                     "update_time": ts(r.get("updateTime"))})
    if rows:
        with engine.begin() as c:
            c.execute(text("SET LOCAL statement_timeout=0"))
            c.execute(text("""INSERT INTO users(user_id,phone,username,update_time)
                VALUES(:user_id,:phone,:username,:update_time)
                ON CONFLICT(user_id) DO UPDATE SET
                  phone=COALESCE(EXCLUDED.phone,users.phone),
                  username=COALESCE(EXCLUDED.username,users.username),
                  update_time=EXCLUDED.update_time"""), rows)

BATCH = 500  # insert in batches to avoid Supabase timeout

def batch_insert(c, sql, rows):
    for i in range(0, len(rows), BATCH):
        c.execute(text(sql), rows[i:i+BATCH])
        print(f"    inserted {min(i+BATCH, len(rows))}/{len(rows)}")

def sync_deposits(df):
    rows = []
    for _, r in df.iterrows():
        uid = r.get("UserId") or r.get("userId")
        ct = ts(r.get("createTime"))
        if uid is None or pd.isna(uid) or not ct: continue
        rows.append({"user_id": int(uid),
                     "username": safe(r.get("username") or r.get("nickName"), 100),
                     "phone": safe(r.get("userPhone"), 20),
                     "amount": num(r.get("RechargeAmount") or r.get("amount")),
                     "status": safe(r.get("status"), 50),
                     "channel": safe(r.get("channelName") or r.get("channel"), 100),
                     "create_time": ct, "update_time": ts(r.get("updateTime"))})
    if rows:
        with engine.begin() as c:
            batch_insert(c, """INSERT INTO deposits(user_id,username,phone,amount,status,channel,create_time,update_time)
                VALUES(:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                ON CONFLICT(user_id,create_time) DO UPDATE SET
                  amount=EXCLUDED.amount,status=EXCLUDED.status,update_time=EXCLUDED.update_time""", rows)
    return len(rows)

def sync_withdrawals(df):
    rows = []
    for _, r in df.iterrows():
        uid = r.get("UserId") or r.get("userId")
        ct = ts(r.get("createTime"))
        if uid is None or pd.isna(uid) or not ct: continue
        rows.append({"user_id": int(uid),
                     "username": safe(r.get("username") or r.get("bankName"), 100),
                     "phone": safe(r.get("userPhone"), 20),
                     "amount": num(r.get("WithDrawAmount") or r.get("withdrawAmount")),
                     "status": safe(r.get("0 Under review, 1 Payment processing, 2 Completed, 3 Rejected, 4 Failed") or r.get("status"), 50),
                     "channel": safe(r.get("Withdraw Payment Channels") or r.get("channel"), 100),
                     "create_time": ct, "update_time": ts(r.get("updateTime"))})
    if rows:
        with engine.begin() as c:
            batch_insert(c, """INSERT INTO withdrawals(user_id,username,phone,amount,status,channel,create_time,update_time)
                VALUES(:user_id,:username,:phone,:amount,:status,:channel,:create_time,:update_time)
                ON CONFLICT(user_id,create_time) DO UPDATE SET
                  amount=EXCLUDED.amount,status=EXCLUDED.status,update_time=EXCLUDED.update_time""", rows)
    return len(rows)

def sync_wallet(df):
    rows = []
    for _, r in df.iterrows():
        uid = r.get("UserId") or r.get("userId")
        if uid is None or pd.isna(uid): continue
        rows.append({"user_id": int(uid),
                     "username": safe(r.get("Game Name") or r.get("username"), 100),
                     "phone": safe(r.get("userPhone"), 20),
                     "balance": num(r.get("changeAfter") or r.get("balance")),
                     "total_deposits": 0.0, "total_withdrawals": 0.0,
                     "update_time": ts(r.get("updateTime"))})
    if rows:
        with engine.begin() as c:
            batch_insert(c, """INSERT INTO wallet_details(user_id,username,phone,balance,total_deposits,total_withdrawals,update_time)
                VALUES(:user_id,:username,:phone,:balance,:total_deposits,:total_withdrawals,:update_time)
                ON CONFLICT(user_id) DO UPDATE SET
                  balance=EXCLUDED.balance,update_time=EXCLUDED.update_time""", rows)
    return len(rows)

def save_status(status):
    with engine.begin() as c:
        c.execute(text("UPDATE pipeline_config SET last_sync=NOW(),last_status=:s WHERE id=1"), {"s": status})

results = {}
for name, url in APIS.items():
    print(f"\n[{name}] Fetching {url}")
    try:
        df = fetch(url)
        print(f"  Rows: {len(df)}, Columns: {df.columns.tolist()[:5]}")
        upsert_users(df)
        if name == "deposits":    results[name] = sync_deposits(df)
        elif name == "withdrawals": results[name] = sync_withdrawals(df)
        elif name == "wallet":    results[name] = sync_wallet(df)
        print(f"  ✓ Saved {results[name]} records")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results[name] = f"Error: {e}"

status = " | ".join(f"{k}: {v} synced" if isinstance(v,int) else f"{k}: {v}" for k,v in results.items())
save_status(status)
print(f"\nDone: {status}")

# Exit with error if all APIs failed (so GitHub shows red X)
if all(isinstance(v, str) and "Error" in v for v in results.values()):
    sys.exit(1)
