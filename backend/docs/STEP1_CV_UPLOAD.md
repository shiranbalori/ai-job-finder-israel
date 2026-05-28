# Step 1 — CV Upload, Extraction & SQLite

Real CV upload pipeline for **AI Job Finder Israel**.

## Prerequisites

- Python 3.11+
- Project root `.env` (copy from `.env.example`)

## Install & run

```powershell
# From project root
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/docs | Swagger UI (interactive API) |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/health | Health check |

SQLite database: `backend/data/app.db`  
Uploaded files: `backend/uploads/`

## Database tables

| Table | Purpose |
|-------|---------|
| `cv_profiles` | Extracted CV data + raw text |
| `jobs` | Job listings (seeded on first run) |
| `job_matches` | CV ↔ job scores |
| `user_settings` | Email prefs, demo flag |

## Endpoints (Step 1)

### POST `/api/cv/upload`

Upload PDF or DOCX → extract text → parse fields → save → match jobs.

**Request:** `multipart/form-data` with field `file`

**Response:**
```json
{
  "cv_profile": { "id": 1, "full_name": "...", "skills": [...], "is_demo": false },
  "matches": [...],
  "total_jobs_scored": 10,
  "message": "...",
  "extraction_method": "mock_heuristic"
}
```

**curl example:**
```bash
curl -X POST http://127.0.0.1:8000/api/cv/upload \
  -F "file=@resume.pdf"
```

**PowerShell example:**
```powershell
curl.exe -X POST http://127.0.0.1:8000/api/cv/upload -F "file=@C:\path\to\resume.docx"
```

### POST `/api/cv/extract`

Extract only (optional `save=true` to persist).

```bash
curl -X POST http://127.0.0.1:8000/api/cv/extract \
  -F "raw_text=Demo Candidate, ML Engineer, 5 years Python PyTorch NLP, fluent Hebrew and English" \
  -F "save=false"
```

### GET `/api/cv/latest`

Returns the most recently uploaded profile (or `null`).

### GET `/api/cv/{id}`

Profile by database ID.

## Extraction pipeline

1. **Validate** — PDF/DOCX only, max 10 MB (configurable via `MAX_UPLOAD_BYTES`)
2. **Save** — `backend/uploads/{uuid}.pdf|docx`
3. **Extract text**
   - PDF: `pypdf.PdfReader`
   - DOCX: `python-docx`
4. **Parse fields** — skills, tools, job titles, years, email, name, languages
   - Default: heuristic parser (`AI_PROVIDER=mock`)
   - Optional: OpenAI/Gemini when `AI_PROVIDER=openai|gemini` and API key set
5. **Persist** — `cv_profiles` row (`is_demo=false`)
6. **Match** — score all active jobs → `job_matches`
7. **Real Mode** — sets `user_settings.demo_mode = false`

## Connect frontend (Real Mode)

```powershell
cd frontend
copy .env.example .env
# Ensure: VITE_USE_MOCK=false
npm install
npm run dev
```

Open http://localhost:5173 → **Upload CV** (not Demo Mode).

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Only PDF and DOCX files are supported` | Wrong extension | Use `.pdf` or `.docx` |
| `Could not extract text` | Scanned PDF / empty file | Use text-based PDF or DOCX |
| `File too large` | Over 10 MB | Reduce file size or raise `MAX_UPLOAD_BYTES` |
| CORS error | Frontend origin not allowed | Add origin to `CORS_ORIGINS` in `.env` |

## Tests (manual)

```powershell
# Health
curl http://127.0.0.1:8000/health

# Text-only extract
curl -X POST http://127.0.0.1:8000/api/cv/extract `
  -F "raw_text=Demo Candidate demo.candidate@example.com Machine Learning Engineer 5 years Python PyTorch NLP Docker Git Hebrew English" `
  -F "save=true"
```
