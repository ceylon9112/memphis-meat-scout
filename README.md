# Memphis Meat Scout

Mobile-first Progressive Web App for finding verified meat deals in the Greater Memphis area.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | FastAPI + Python 3.11 |
| Database | MongoDB (local dev) / MongoDB Atlas (production) |
| PWA | vite-plugin-pwa + Workbox |

## Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB running locally on `mongodb://localhost:27017`

## Quick Start

**Terminal 1 — Backend:**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173  
API: http://localhost:8000  
Admin: http://localhost:5173/admin/login  
Default credentials: `admin` / `changeme`

## PWA Icons

Add these two files to `frontend/public/` for full PWA installability:
- `pwa-192x192.png` — 192×192px app icon
- `pwa-512x512.png` — 512×512px app icon (maskable)
- `apple-touch-icon.png` — 180×180px for iOS

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and update:

| Variable | Description |
|----------|-------------|
| `MONGODB_URL` | MongoDB connection string |
| `DATABASE_NAME` | Database name (default: `memphis_meat_scout`) |
| `JWT_SECRET_KEY` | **Change before production** |
| `ADMIN_USERNAME` | Admin login username |
| `ADMIN_PASSWORD` | Admin login password |

## Routes

| Path | Description |
|------|-------------|
| `/` | Deal feed + Cookout Forecast |
| `/cuts` | Browse meat cuts |
| `/cuts/:id` | Cut price comparison |
| `/stores` | Vendor directory |
| `/admin/login` | Admin login |
| `/admin/dashboard` | Stats + alerts |
| `/admin/deals` | Deal management |
| `/admin/vendors` | Vendor management |
| `/admin/cuts` | Cut management |

## Deal Freshness

A deal is **active** if its `verified_date` is within the last 7 calendar days (inclusive).  
Deals older than 7 days are silently excluded from the public feed.

## Notes

- NWS User-Agent email is set to `contact@memphismeatscout.com` — update in `backend/app/services/weather.py`
- Weather data is cached server-side for 3 hours
- Last-fetched deal data is readable offline via service worker cache
