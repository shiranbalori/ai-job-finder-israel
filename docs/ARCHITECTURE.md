# Architecture — AI Job Finder Israel

## Purpose

Portfolio-ready full-stack app that parses a CV, matches Israeli AI/Data/Automation jobs, explains scores, and supports a daily email digest.

## Components

### Frontend (`frontend/`)

- **React + Vite + TypeScript + Tailwind**
- Pages: Landing, Dashboard, Upload, Job Details, Settings, Architecture
- **i18n**: English + Hebrew with `dir="rtl"` for Hebrew
- **Demo Mode** button calls `POST /api/demo/activate`
- Vite dev proxy forwards `/api` and `/health` to FastAPI

### Backend (`backend/app/`)

| Module | Responsibility |
|--------|----------------|
| `routers/cv.py` | PDF/DOCX upload, parsing, rematch |
| `routers/jobs.py` | List/filter jobs |
| `routers/matches.py` | Match results + dashboard stats |
| `routers/demo.py` | One-click demo activation |
| `routers/settings.py` | User prefs + manual digest trigger |
| `services/cv_parser.py` | Text extraction + heuristic parse |
| `services/ai_client.py` | OpenAI / Gemini / mock abstraction |
| `services/job_matcher.py` | Scoring + DB persistence |
| `services/email_service.py` | SMTP or console preview |
| `seed/` | Demo CV + 10 Israeli tech jobs |

### Database (SQLite)

- `cv_profiles` — parsed CV data
- `jobs` — listings (seeded mock data)
- `job_matches` — scores, reasons, missing skills
- `user_settings` — email, digest, language, demo flag

## AI workflow

```
Upload → Extract text → Parse profile (AI or heuristic)
       → Load jobs → Match each job (AI or heuristic)
       → Save matches → Display in UI
       → (Scheduled) Email new matches
```

### Providers

Set `AI_PROVIDER` in `.env`:

- `mock` — no API keys; heuristic parser + matcher (default, interview-safe)
- `openai` — GPT extracts profile and scores jobs
- `gemini` — Google Generative Language API

## Email workflow

- APScheduler cron at `DAILY_EMAIL_HOUR` (UTC)
- When `DAILY_EMAIL_ENABLED=false` or SMTP is placeholder, body is **logged** not sent
- `POST /api/settings/send-digest` triggers a manual test

## Security notes (portfolio)

- No auth (single-user demo)
- File uploads stored in `backend/uploads/` with UUID names
- CORS limited to local Vite origins
- Do not commit `.env` with real API keys

## Extension ideas

- Live job scrapers (Drushim, LinkedIn API)
- User accounts (JWT)
- WebSocket progress during CV analysis
- Vector embeddings for semantic match
