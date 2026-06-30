#!/bin/bash
# ============================================================
# Oracle Database Setup - Create schema and admin user
# Run AFTER Oracle DB XE is installed and running
# Run as: sudo bash setup-oracle-db.sh
# ============================================================

set -e

echo "======================================================"
echo "  Oracle DB - Create Schema"
echo "======================================================"

# Load .env
source /opt/lottery/backend/.env

echo "[1/3] Creating Oracle DB user: $ORACLE_USER"
sqlplus / as sysdba <<EOF
-- Create tablespace
CREATE TABLESPACE lottery_ts
  DATAFILE '/opt/oracle/oradata/XE/lottery_ts.dbf'
  SIZE 500M AUTOEXTEND ON NEXT 100M MAXSIZE 5G;

-- Create user
CREATE USER $ORACLE_USER IDENTIFIED BY "$ORACLE_PASSWORD"
  DEFAULT TABLESPACE lottery_ts
  QUOTA UNLIMITED ON lottery_ts;

-- Grant privileges
GRANT CONNECT, RESOURCE, CREATE SESSION TO $ORACLE_USER;
GRANT CREATE TABLE, CREATE INDEX, CREATE SEQUENCE TO $ORACLE_USER;

EXIT;
EOF

echo "[2/3] Creating tables and indexes..."
sqlplus "$ORACLE_USER/$ORACLE_PASSWORD@localhost:$ORACLE_PORT/$ORACLE_SERVICE" @/opt/lottery/backend/db/schema.sql

echo "[3/3] Creating admin user (password: Admin@123)..."
source /opt/lottery/venv/bin/activate
python3 -c "
import oracledb, os
from passlib.context import CryptContext

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
hashed = pwd.hash('Admin@123')

conn = oracledb.connect(
    user=os.environ['ORACLE_USER'],
    password=os.environ['ORACLE_PASSWORD'],
    dsn=f\"{os.environ['ORACLE_HOST']}:{os.environ['ORACLE_PORT']}/{os.environ['ORACLE_SERVICE']}\"
)
cur = conn.cursor()
cur.execute(\"DELETE FROM ADMIN_USERS WHERE username = 'admin'\")
cur.execute(
    \"INSERT INTO ADMIN_USERS (username, password_hash, role) VALUES ('admin', :1, 'superadmin')\",
    [hashed]
)
conn.commit()
conn.close()
print('Admin user created: admin / Admin@123')
print('CHANGE THIS PASSWORD after first login!')
"

echo ""
echo "======================================================"
echo "  Database ready!"
echo "  Login: admin / Admin@123  (change immediately)"
echo "======================================================"
