# Job fetching architecture

Real jobs are fetched from public Greenhouse and Lever job board APIs, filtered, deduplicated, and stored in SQLite. Demo seed jobs remain as fallback for Demo Mode.

## Layout

```
adapters/          # Greenhouse, Lever API clients
services/          # job_fetch_service, job_filter, job_search_service
repositories/      # job_repository (SQLite upsert + dedup)
domain/            # FetchedJobDTO normalized shape
```

## Flow

1. `POST /api/jobs/refresh` → `JobFetchService.refresh()`
2. Each adapter fetches all open roles from configured boards
3. `job_filter.filter_fetched_jobs()` keeps AI/Data roles **with Israel-only locations**
   - Includes: Israel, IL, Tel Aviv, Herzliya, Haifa, Remote Israel, Hybrid, etc.
   - Excludes: global remote, US, UK, Europe, India, etc.
4. Logs: `fetched`, `israel`, `excluded` per source
5. `JobRepository.upsert_fetched()` dedupes by `(source, external_id)` then URL
5. Demo jobs (`source=seed`, `is_demo=true`) are never modified

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs/refresh` | Fetch from Greenhouse + Lever |
| GET | `/api/jobs` | List jobs (excludes demo by default) |
| GET | `/api/jobs/search` | Search with `q`, `category`, `work_mode`, `source` |
| GET | `/api/jobs/mock` | Demo seed jobs only |

## Configuration (`.env`)

```env
GREENHOUSE_BOARD_TOKENS=riskified,taboola,similarweb
LEVER_COMPANY_SLUGS=wix,gong,lemonade
JOB_FETCH_ON_STARTUP=false
```

Empty values use built-in defaults in `config.py`.

## Logs

Each refresh logs per source:

- boards queried
- jobs fetched (raw count)
- jobs matched (after filters)
- created / updated counts
- per-board errors (404 boards are skipped, others continue)

## Frontend

- **Demo Mode** → `GET /api/jobs/mock`
- **Real Mode** → `GET /api/jobs` (fetched jobs)
- **Refresh** → Dashboard “Refresh live jobs” button → `POST /api/jobs/refresh`
- **Badges** → `JobSourceBadge`: Demo vs Live · Greenhouse/Lever
