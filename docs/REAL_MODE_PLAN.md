# Real Mode Implementation Plan

This document describes how **AI Job Finder Israel** evolves from interview **Demo Mode** to a **Real Mode** production app — without removing demo functionality.

## Modes

| Mode | Purpose | Trigger |
|------|---------|---------|
| **Demo Mode** | Portfolio / interview — demo candidate profile, curated matches | `POST /api/demo/activate` or Demo button |
| **Real Mode** | Actual usage — user uploads their CV | `POST /api/cv/upload` |

Demo Mode stays available at all times. Real upload clears `demo_mode` in settings and sets `is_demo=false` on the CV profile.

---

## Architecture overview

```
Frontend (React)          Backend (FastAPI)              SQLite
─────────────────         ─────────────────              ──────
UploadPage ─────────────► POST /api/cv/upload ─────────► cv_profiles
Dashboard  ◄──────────────  extract + match  ◄────────── job_matches
Settings   ─────────────► PATCH /api/settings ───────► user_settings
Demo btn   ─────────────► POST /api/demo/activate
```

---

## Step-by-step roadmap

### Step 1 — CV upload + extraction + SQLite ✅ (this step)

**Goal:** Real PDF/DOCX upload, text extraction, structured parsing, persistence.

| Item | Status |
|------|--------|
| FastAPI app + SQLite | Done |
| `POST /api/cv/upload` | Done + hardened |
| PDF extraction (`pypdf`) | Done |
| DOCX extraction (`python-docx`) | Done |
| Parse skills, tools, titles, experience, languages | Done (heuristic; live AI optional) |
| Save to `cv_profiles` | Done |
| Auto-match against seeded jobs | Done |
| OpenAPI docs at `/docs` | Done |
| Clear demo flag on real upload | Done |

**Run:** see [backend/docs/STEP1_CV_UPLOAD.md](../backend/docs/STEP1_CV_UPLOAD.md)

---

### Step 2 — Job search service (planned)

- Adapter interface: `JobSource.fetch_jobs() -> list[Job]`
- Implementations: `MockJobSource` (fallback), `PlaceholderApiSource` (env-based URL/key)
- Optional: one public API (e.g. Adzuna, Remotive) when key present
- `POST /api/jobs/sync` to ingest into SQLite
- Frontend Real Mode loads `/api/jobs` not `/api/jobs/mock`

---

### Step 3 — Real matching (planned)

- Skill overlap + description similarity
- Live AI matching when `AI_PROVIDER=openai|gemini`
- Persist explainable reasons + missing skills (already in schema)
- Recalculate via `POST /api/matches/calculate`

---

### Step 4 — Email + settings (planned)

- Settings page → `PATCH /api/settings` (email, min score, digest toggle)
- SMTP from `.env`: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, …
- `POST /api/email/daily` sends real digest (not console-only)

---

### Step 5 — Daily scheduler (planned)

- APScheduler cron at `DAILY_EMAIL_HOUR`
- Flow: sync jobs → match all CVs → send email
- Structured logs to stdout / file

---

## Environment variables (Real Mode)

```env
# Backend
AI_PROVIDER=mock          # mock | openai | gemini
DATABASE_URL=sqlite:///./data/app.db
MAX_UPLOAD_BYTES=10485760 # 10 MB

# Optional live AI
OPENAI_API_KEY=
GEMINI_API_KEY=

# Frontend (do not set VITE_USE_MOCK for real usage)
VITE_USE_MOCK=false
VITE_API_BASE_URL=
```

---

## Frontend integration rules

1. **Do not rewrite UI** — connect existing pages to live API.
2. **`uploadCV`** — must not fall back to mock (surface errors).
3. **`refresh()`** — use `/api/jobs` when not in demo mode.
4. **Demo Mode button** — unchanged; calls `/api/demo/activate`.
