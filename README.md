# AI Job Finder Israel

Portfolio-ready web app: upload a CV, get AI-ranked **AI / Data / Automation** jobs in Israel (0–100 match score), explainable reasons, missing skills, and a daily email digest.

![Demo ready](https://img.shields.io/badge/demo-ready-success)
![Stack](https://img.shields.io/badge/React-Vite-61DAFB)
![Stack](https://img.shields.io/badge/FastAPI-009688)
![i18n](https://img.shields.io/badge/EN%20%7C%20HE-blue)

## Screenshots

> Add captures to `screenshots/` (see `screenshots/README.md`).

| Landing | Dashboard | Job detail |
|---------|-----------|------------|
| `screenshots/landing.png` | `screenshots/dashboard.png` | `screenshots/job-detail.png` |

## Features

- Upload CV (PDF / DOCX) → extract skills, experience, titles, tools
- Mock Israeli tech jobs (Monday.com, AI21, Wix, Mobileye, …)
- Match score 0–100 + explanation + missing skills
- SQLite persistence (local) / PostgreSQL on Supabase (production)
- Daily email digest (SMTP placeholder — logs in dev)
- English + Hebrew UI (RTL)
- **Demo Mode** — works without API keys

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| Database | SQLite (local) / PostgreSQL via Supabase (production) |
| AI | OpenAI / Gemini / **mock** (default) |
| Email | aiosmtplib + APScheduler |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design and AI workflow.

## Project structure

```
ai-job-finder-israel/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routers/          # REST endpoints
│   │   ├── services/         # CV parse, match, AI, email
│   │   └── seed/             # Demo jobs + CV
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   └── src/
│       ├── pages/            # 6 routes
│       ├── components/
│       └── i18n/
├── docs/
├── screenshots/
├── .env.example
└── README.md
```

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- (Optional) OpenAI or Gemini API key for live AI matching

---

## Step 1 — Clone & environment file

From the project root:

```powershell
cd "c:\Users\shira\OneDrive\שולחן העבודה\ai-job-finder-israel"
copy .env.example .env
```

Edit `.env` if needed. Defaults use `AI_PROVIDER=mock` (no keys required).

---

## Step 2 — Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the API (keep this terminal open):

```powershell
python run.py
```

API docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/health

---

## Step 2 — Frontend ↔ Backend (Real Mode)

See [docs/RUN_LOCAL.md](docs/RUN_LOCAL.md) for running both servers together.

CV upload service: `frontend/src/api/cvService.ts` → `uploadRealCV()`.

---

## Step 3 — Frontend setup

Open a **new** terminal:

```powershell
cd "c:\Users\shira\OneDrive\שולחן העבודה\ai-job-finder-israel\frontend"
npm install
npm run dev
```

App: http://localhost:5173

---

## Step 4 — Connect frontend to backend

Run **both** terminals:

```powershell
# Terminal 1 — backend
cd backend
.\.venv\Scripts\Activate.ps1
python run.py

# Terminal 2 — frontend
cd frontend
copy .env.example .env
npm run dev
```

Ensure `frontend/.env` has `VITE_USE_MOCK=false` (default). The dashboard loads jobs from `GET /api/jobs/mock` and matches from `GET /api/matches`. CV upload posts to `POST /api/cv/upload` and displays extracted skills + scores.

---

## Step 5 — Try Demo Mode

1. Open http://localhost:5173
2. Click **Try Demo Mode** (header)
3. Go to **Dashboard** — see ranked Israeli AI/Data jobs

No CV file or API keys needed.

---

## Configuration

| Variable | Description |
|----------|-------------|
| `APP_ENV` | `development` (SQLite) \| `production` (PostgreSQL) |
| `DATABASE_URL` | `sqlite:///./data/app.db` locally, Supabase URI in production |
| `DB_USE_NULL_POOL` | `true` for Supabase transaction pooler (port 6543) |
| `AI_PROVIDER` | `mock` \| `openai` \| `gemini` |
| `OPENAI_API_KEY` | For OpenAI parsing/matching |
| `GEMINI_API_KEY` | For Gemini |
| `DAILY_EMAIL_ENABLED` | `true` to enable scheduler emails |
| `SMTP_*` | Real SMTP when ready |
| `VITE_API_URL` | Production backend URL (Vercel). Leave empty in dev (uses Vite proxy via `VITE_DEV_API_URL`) |

## API highlights

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check + DB status |
| POST | `/api/cv/upload` | Upload PDF/DOCX, extract, match |
| POST | `/api/cv/extract` | Extract CV fields (mock AI) |
| GET | `/api/jobs/mock` | Mock Israeli AI/Data jobs |
| GET | `/api/jobs/{id}` | Job details |
| POST | `/api/matches/calculate` | Calculate match scores 0–100 |
| PUT | `/api/preferences` | Save user preferences |
| POST | `/api/email/daily` | Daily email placeholder |
| POST | `/api/demo/activate` | One-click demo |

Full reference: [backend/docs/API.md](backend/docs/API.md)

## Production deployment

Deploy **frontend → Vercel**, **backend → Render**, **database → Supabase**.

| Platform | Root directory | Config |
|----------|----------------|--------|
| Vercel | `frontend/` | `frontend/vercel.json`, `VITE_API_URL` |
| Render | `backend/` | `render.yaml`, env from `backend/.env.production.example` |

Full step-by-step guide: **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** (migrations, CORS, env vars, checklist).

---

## Supabase setup (production database)

Local development stays on **SQLite** (`DATABASE_URL=sqlite:///./data/app.db`). Production uses **PostgreSQL on Supabase**. Do **not** put Supabase credentials in `backend/.env` while developing locally.

### 1. Create a Supabase project

1. Sign in at [supabase.com](https://supabase.com) → **New project**
2. Pick a region (e.g. Europe / Frankfurt)
3. Save the **database password**

### 2. Get connection values

In **Settings → Database → Connection string → URI**, copy the **Transaction pooler** URL (port **6543**):

```text
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
```

You will also need:

| Variable | Value |
|----------|--------|
| `APP_ENV` | `production` |
| `DATABASE_URL` | Pooler URI above |
| `DB_USE_NULL_POOL` | `true` |
| `JWT_SECRET` | Long random string |
| `CORS_ORIGINS` | Your Vercel frontend URL |

Template: `backend/.env.production.example`

### 3. Where to paste (when deploying — not yet)

Paste env vars on **Render** (Web Service → Environment), not in local `backend/.env`.

### 4. Migration flow (run once before first deploy)

From a shell with production env vars loaded (Render shell, or temporary export):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Verify connection
python scripts/db_check.py

# 2. Create all PostgreSQL tables
python scripts/db_init.py
```

If `db_init.py` fails on port 6543, set `MIGRATION_DATABASE_URL` to the **direct** Supabase URL (port **5432**, host `db.[PROJECT-REF].supabase.co`) and run `db_init.py` again.

Confirm tables in Supabase **Table Editor** (`users`, `jobs`, `cv_profiles`, `job_matches`, …).

### 5. Safety checks

The backend **refuses to start** when `APP_ENV=production` and `DATABASE_URL` is SQLite — this prevents accidental production use of the local file database.

| Command | Purpose |
|---------|---------|
| `python scripts/db_check.py` | Test DB connection (SQLite or PostgreSQL) |
| `python scripts/db_init.py` | Initialize PostgreSQL schema (Alembic) — **run manually, not on startup** |
| `python scripts/db_upgrade.py` | Alias for `db_init.py` |

Migrations are **not** run automatically when the API starts (prevents Supabase pooler hangs). Set `DB_RUN_MIGRATIONS_ON_STARTUP=true` only if you explicitly want startup migrations.

---

## Production build (local preview)

```powershell
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm run preview
```

## Interview talking points

1. **Mock-first design** — heuristic CV parser + skill overlap matcher for reliable demos
2. **AI abstraction** — swap `AI_PROVIDER` without code changes
3. **Explainable matching** — score, reason, matched/missing skills stored in DB
4. **i18n** — Hebrew job (Mobileye) + RTL layout
5. **Email pipeline** — scheduler + safe placeholder when SMTP not configured

## License

MIT — portfolio / educational use.
