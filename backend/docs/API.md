# API Reference — AI Job Finder Israel

Base URL: `http://127.0.0.1:8000`  
OpenAPI UI: `http://127.0.0.1:8000/docs`

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | API + SQLite status |
| GET | `/api/health` | Alias |

## CV

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cv/upload` | Upload PDF/DOCX → extract → save → match all jobs |
| POST | `/api/cv/extract` | Extract fields only (`file` or `raw_text`, optional `save=true`) |
| GET | `/api/cv/latest` | Latest saved profile |
| GET | `/api/cv/{id}` | Profile by ID |

### Upload example (Real Mode)

```bash
curl -X POST http://127.0.0.1:8000/api/cv/upload \
  -F "file=@resume.pdf"
```

Response includes `extraction_method` (`mock_heuristic` or `live_ai`) and sets `is_demo=false`.

See [docs/STEP1_CV_UPLOAD.md](../docs/STEP1_CV_UPLOAD.md) for full Step 1 guide.

## Jobs (mock data in SQLite)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/jobs/mock` | Seeded Israeli AI/Data jobs |
| GET | `/api/jobs` | All active jobs (filters: category, language, search) |
| GET | `/api/jobs/{id}` | **Job details** |
| GET | `/api/jobs/categories` | Category list |

## Matches

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/matches/calculate` | **Calculate scores** for a CV profile |
| GET | `/api/matches` | List saved matches |
| GET | `/api/matches/stats/dashboard` | Dashboard stats |
| GET | `/api/matches/{id}` | Single match |

### Calculate example

```bash
curl -X POST http://127.0.0.1:8000/api/matches/calculate \
  -H "Content-Type: application/json" \
  -d '{"cv_profile_id": 1, "min_score": 50}'
```

## Preferences & email

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/settings` | Get preferences |
| PATCH | `/api/settings` | Partial update |
| PUT | `/api/preferences` | Save preferences (alias) |
| POST | `/api/email/daily` | **Daily email placeholder** |
| POST | `/api/settings/send-digest` | Legacy alias |

## Demo

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/demo/activate` | Load demo CV + matches |
| POST | `/api/demo/deactivate` | Turn off demo flag |

## Mock AI

Set in `.env`:

```env
AI_PROVIDER=mock
```

CV extraction uses keyword heuristics (`app/services/mock_ai.py`).  
Matching uses skill overlap scoring (0–100) with explainable reasons.
