# Oracle Cloud VM Setup Guide

## Prerequisites
- Oracle Cloud Always Free account
- Ubuntu 22.04 VM (ARM Ampere — 4 OCPU, 24GB RAM)
- A domain name pointed to your VM's public IP (optional but recommended)

## Step-by-Step Instructions

### 1. Create Oracle Cloud VM
1. Log in to https://cloud.oracle.com
2. Go to **Compute → Instances → Create Instance**
3. Choose **Ubuntu 22.04** image
4. Shape: **VM.Standard.A1.Flex** (Always Free) — set 4 OCPU, 24GB RAM
5. Add your SSH public key
6. Click **Create**
7. Note the **Public IP address**

### 2. Open Firewall Ports (Oracle Cloud Security List)
Go to **Networking → VCN → Security Lists → Add Ingress Rules:**
| Protocol | Port | Description |
|---|---|---|
| TCP | 22 | SSH |
| TCP | 80 | HTTP |
| TCP | 443 | HTTPS |
| TCP | 8000 | FastAPI (temporary, can remove after Nginx setup) |

### 3. SSH Into Your VM
```bash
ssh ubuntu@YOUR_VM_PUBLIC_IP
```

### 4. Run Setup Script
```bash
git clone https://github.com/Professornoxx/lotteryUsers.git /opt/lottery
sudo bash /opt/lottery/server/setup.sh
```

### 5. Configure Environment
```bash
nano /opt/lottery/backend/.env
```
Fill in all values (Oracle DB credentials, JWT secret, Cloudinary keys).

### 6. Setup Oracle Database
```bash
sudo bash /opt/lottery/server/setup-oracle-db.sh
```

### 7. Start the Service + Nginx
```bash
# Replace yourdomain.com with your actual domain or VM IP
sudo bash /opt/lottery/server/setup-service.sh yourdomain.com
```

### 8. Import Excel Data
```bash
# Upload your Excel file to the VM first:
# scp /path/to/lotteryUserInfo.xlsx ubuntu@YOUR_VM_IP:/tmp/

cd /opt/lottery/backend
source /opt/lottery/venv/bin/activate
python db/import_excel.py --file /tmp/lotteryUserInfo.xlsx
```

### 9. Setup GitHub Actions Secrets
Go to your GitHub repo → **Settings → Secrets → Actions** and add:

| Secret | Value |
|---|---|
| `ORACLE_VM_HOST` | Your VM public IP |
| `ORACLE_VM_USER` | `ubuntu` |
| `ORACLE_VM_SSH_KEY` | Your private SSH key (paste full content) |
| `VERCEL_TOKEN` | From vercel.com → Settings → Tokens |
| `VERCEL_ORG_ID` | From Vercel project settings |
| `VERCEL_PROJECT_ID` | From Vercel project settings |

### Useful Commands
```bash
# Check API status
systemctl status lottery-api

# View live logs
journalctl -u lottery-api -f

# Restart API
sudo systemctl restart lottery-api

# Test API
curl http://localhost:8000/
```
