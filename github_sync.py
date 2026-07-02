"""
GitHub Actions sync — uses Supabase REST API for fast HTTP upserts.
No database connection needed — avoids all timeout/connection issues.
"""
import os, io, math, requests, sys, json
from datetime import date
import pandas as pd

TOKEN   = os.environ["BEARER_TOKEN"]
SB_KEY  = os.environ["SB_SERVICE_KEY"]
TODAY   = date.today().strftime("%Y-%m-%d")
SB_URL  = "https://dglehhqpwdsyuezzupje.supabase.co/rest/v1"
SB_HDR  = {
    "apikey": SB_KEY,
    "Authorization": f"Bearer {SB_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

APIS = {
    "deposits":    "https://api.rumanagers.online/prod-api/business/water/export",
    "withdrawals": "https://api.rumanagers.online/prod-api/business/withdraw/export",
    "wallet":      "https://api.rumanagers.online/prod-api/business/detail/export",
}
PAYLOAD = {"packageId": 10, "pageNum": 1, "pageSize": 5000,
           "useUpiQuery": True, "queryDate": [TODAY, TODAY]}
API_HDR = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

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
        return None if str(r) == "NaT" else r.isoformat()
    except: return None

def sb_upsert(table, rows, batch=200):
    """HTTP upsert to Supabase REST API in batches."""
    total = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i+batch]
        r = requests.post(f"{SB_URL}/{table}", headers=SB_HDR,
                          data=json.dumps(chunk), timeout=30)
        if r.status_code not in (200, 201):
            print(f"  Supabase error {r.status_code}: {r.text[:200]}")
        else:
            total += len(chunk)
            print(f"  upserted {min(i+batch, len(rows))}/{len(rows)}")
    return total

def fetch(url):
    r = requests.post(url, headers=API_HDR, json=PAYLOAD, timeout=180)
    print(f"  HTTP {r.status_code} — {len(r.content):,} bytes")
    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")
    if r.content[:2] != b"PK":
        raise Exception(f"Not Excel ({len(r.content)} bytes): {r.content[:50]}")
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")

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
                     "create_time": ct,
                     "update_time": ts(r.get("updateTime"))})
    return sb_upsert("deposits", rows)

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
                     "create_time": ct,
                     "update_time": ts(r.get("updateTime"))})
    return sb_upsert("withdrawals", rows)

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
    return sb_upsert("wallet_details", rows)

def save_status(status):
    r = requests.patch(f"{SB_URL}/pipeline_config?id=eq.1", headers=SB_HDR,
                       data=json.dumps({"last_sync": date.today().isoformat(),
                                        "last_status": status}), timeout=10)
    print(f"  Status saved: {r.status_code}")

# ── Main ────────────────────────────────────────────────────────────────────
results = {}
for name, url in APIS.items():
    print(f"\n[{name}] {url}")
    try:
        df = fetch(url)
        print(f"  Rows: {len(df)}")
        if name == "deposits":      results[name] = sync_deposits(df)
        elif name == "withdrawals": results[name] = sync_withdrawals(df)
        elif name == "wallet":      results[name] = sync_wallet(df)
        print(f"  ✓ {results[name]} records saved")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results[name] = f"Error: {e}"

status = " | ".join(f"{k}: {v} synced" if isinstance(v,int) else f"{k}: {v}"
                    for k,v in results.items())
save_status(status)
print(f"\nDone: {status}")

if all(isinstance(v,str) and "Error" in v for v in results.values()):
    sys.exit(1)
