# Lottery Users Dashboard

A full-stack dashboard for managing and monitoring lottery user data.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite (deployed on Vercel) |
| Backend | FastAPI (Oracle Cloud VM) |
| Auth | JWT Authentication |
| Database | Oracle Database |
| Media | Cloudinary |
| CI/CD | GitHub Actions |

## Project Structure

```
lotteryUsers/
├── frontend/          # React dashboard
├── backend/           # FastAPI REST API
└── .github/workflows/ # CI/CD pipelines
```

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
