# Job collection pipeline

Production service that collects real AI/Data jobs from public APIs.

## Architecture

```
POST /api/jobs/refresh
  → JobCollectorService.collect()
    → GreenhouseAdapter / LeverAdapter / RemoteOKAdapter  (fetch)
    → normalize_collected_job()                         (unified schema)
    → extract_ai_data_tags()                            (Python, LLM, RAG, …)
    → filter_fetched_jobs() / filter_remoteok_jobs()      (AI/Data + Israel)
    → JobRepository.upsert_fetched()                      (dedupe + save)
    → JobCollectorLog                                   (audit trail)
```

## Sources

| Source | API | Default boards |
|--------|-----|----------------|
| `greenhouse` | Greenhouse Job Board API | riskified, taboola, similarweb, jfrog, fireblocks |
| `lever` | Lever Postings API | walkme |
| `remoteok` | remoteok.com/api | RemoteOK AI/Data listings |

## Unified schema (`FetchedJobDTO`)

All sources normalize to:

- `external_id`, `source`, `title`, `company`, `location`
- `description`, `category`, `work_mode`, `url`
- `skills`, `tags`, `requirements`
- `is_israel`, `location_tag`, `posted_at`

## Tags extracted

`Python`, `LLM`, `RAG`, `NLP`, `SQL`, `LangChain`, `GenAI`

Stored in `jobs.tags_json` and merged into `skills_json`.

## Deduplication

1. In-batch: `(source, external_id)` and URL
2. Database: upsert on `(source, external_id)`, fallback URL match

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/jobs/refresh?sources=greenhouse,lever,remoteok` | Run full collection pipeline |
| GET | `/api/jobs/collector/logs` | Recent collector audit logs |
| GET | `/api/jobs?tag=Python` | Filter jobs by AI/Data tag |

## Configuration

```env
GREENHOUSE_BOARD_TOKENS=riskified,taboola,similarweb
LEVER_COMPANY_SLUGS=walkme,gong,wix
JOB_FETCH_ON_STARTUP=true
JOB_REFRESH_ENABLED=true
JOB_REFRESH_INTERVAL_HOURS=4
JOB_COLLECTOR_TIMEOUT_SEC=120
```

## Scheduler

Background refresh every `JOB_REFRESH_INTERVAL_HOURS` via APScheduler (see `app/scheduler.py`).

## Error handling

- Per-board errors collected without aborting other boards
- Per-source timeout (`JOB_COLLECTOR_TIMEOUT_SEC`)
- Partial success when some sources fail
- HTTP 502 when all sources fail; 503 on unexpected exceptions
- All runs logged to `job_collector_logs`
