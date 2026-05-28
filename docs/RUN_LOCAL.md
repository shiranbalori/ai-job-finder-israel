# Run Frontend + Backend Together

How to run **AI Job Finder Israel** in **Real Mode** (live FastAPI + React).

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- Two terminal windows

---

## Terminal 1 — Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Wait until you see Uvicorn running on **http://127.0.0.1:8000**.

Verify:

```powershell
curl http://127.0.0.1:8000/health
```

Open API docs: http://127.0.0.1:8000/docs

---

## Terminal 2 — Frontend (React + Vite)

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open the app: **http://localhost:5173**

### Required `.env` settings (Real Mode)

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=
```

Leave `VITE_API_BASE_URL` empty in development — Vite proxies `/api` and `/health` to port 8000 (see `frontend/vite.config.ts`).

---

## Real Mode vs Demo Mode

| | **Real Mode** | **Demo Mode** |
|---|---------------|---------------|
| How to start | Upload page → drop PDF/DOCX | Landing → **Try Demo Mode** |
| API call | `POST /api/cv/upload` | `POST /api/demo/activate` |
| Needs backend | **Yes** | Yes (or frontend mock if `VITE_USE_MOCK=true`) |
| Your CV | Your file | Sample (demo candidate profile) |

Uploading a real CV **automatically exits Demo Mode** on the backend.

---

## Real upload flow

1. Go to **Upload CV** (`/upload`)
2. Confirm badge shows **Real Mode** + **FastAPI connected**
3. Drop or browse a **PDF** or **DOCX**
4. Loading spinner runs through: Upload → Extract → Match → Done
5. Results show:
   - Parsed profile (name, email, skills, languages)
   - Extracted text preview (expandable)
   - Top job matches from SQLite
6. Click **View all matches on dashboard**

Frontend service: `frontend/src/api/cvService.ts` → `uploadRealCV()`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ERR_CONNECTION_REFUSED` on :5173 | Run `npm run dev` in `frontend/` |
| `Backend is offline` on upload | Run `python run.py` in `backend/` |
| `Real upload requires VITE_USE_MOCK=false` | Set in `frontend/.env`, restart Vite |
| CORS error | Add `http://localhost:5173` to `CORS_ORIGINS` in root `.env` |
| Empty extracted text | Use a text-based PDF (not scanned image) or DOCX |

---

## Production build

```powershell
# Backend
cd backend
python run.py

# Frontend build
cd frontend
# Set VITE_API_BASE_URL=https://your-api.example.com
npm run build
npm run preview
```

In production, set `VITE_API_BASE_URL` to your FastAPI server URL (no Vite proxy).
