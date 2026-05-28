/**
 * Live FastAPI client.
 * In dev, Vite proxies /api and /health to VITE_DEV_API_URL (see vite.config.ts).
 */

import { getStoredToken } from './authService'
import { apiUrl } from './config'

/** Parse FastAPI error payloads (string or validation array). */
function parseErrorDetail(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') return fallback
  const d = data as { detail?: unknown; message?: string }
  if (typeof d.message === 'string') return d.message
  if (typeof d.detail === 'string') return d.detail
  if (Array.isArray(d.detail)) {
    return d.detail
      .map((item) => {
        if (typeof item === 'object' && item && 'msg' in item) {
          return String((item as { msg: string }).msg)
        }
        return String(item)
      })
      .join('; ')
  }
  return fallback
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getStoredToken()
  const headers = new Headers(options?.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(apiUrl(path), { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => null)
    throw new Error(parseErrorDetail(err, res.statusText || 'Request failed'))
  }
  return res.json()
}

export interface SkillConfidence {
  skill: string
  confidence: number
  method: string
}

export interface ExtractionDebug {
  scan_text_len?: number
  raw_regex: string[]
  raw_keyword: string[]
  raw_fuzzy?: string[]
  raw_semantic: string[]
  raw_heuristic?: string[]
  merged?: string[]
  heuristic_merged: string[]
  merged_skills: string[]
  filtered_out: string[]
  priority_missing: string[]
  skills_confidence: SkillConfidence[]
}

export interface ScoreBreakdown {
  skills: number
  semantic: number
  semantic_skills?: number
  embedding?: number
  title: number
  experience: number
  domain?: number
}
export interface JobSkillsDebug {
  scan_text_len?: number
  scan_preview?: string
  raw_regex?: string[]
  raw_keyword?: string[]
  raw_semantic?: string[]
  title_inferred?: string[]
  final_skills?: string[]
}

export interface CVProfile {
  id: number
  full_name: string | null
  email: string | null
  summary: string | null
  years_experience: number | null
  job_titles: string[]
  skills: string[]
  tools: string[]
  technologies: string[]
  languages?: string[]
  language: string
  is_demo: boolean
  source_filename: string | null
  extraction_method?: string
  skills_confidence?: SkillConfidence[]
  created_at: string
}

export interface Job {
  id: number
  title: string
  company: string
  location: string
  description: string
  requirements: string[]
  skills: string[]
  tags?: string[]
  category: string
  employment_type: string
  salary_range: string | null
  url: string | null
  language: string
  is_demo: boolean
  source: string
  work_mode?: string | null
  is_israel?: boolean
  location_tag?: string | null
  posted_at: string
}

export interface JobRefreshResponse {
  total_fetched: number
  total_israel: number
  total_excluded: number
  total_matched: number
  total_created: number
  total_updated: number
  total_skipped?: number
  total_tagged?: number
  duration_ms?: number
  success?: boolean
  partial?: boolean
  log_id?: number | null
  errors?: string[]
  sources: Array<{
    name: string
    boards: string[]
    fetched: number
    matched: number
    israel: number
    excluded: number
    created: number
    updated: number
    skipped?: number
    tagged?: number
    errors: string[]
  }>
  message: string
}

export interface JobSearchResponse {
  items: Job[]
  total: number
  query: string | null
}

export interface JobMatch {
  id: number
  cv_profile_id: number
  job_id: number
  match_score: number
  match_reason: string
  missing_skills: string[]
  matched_skills: string[]
  semantic_matches?: string[]
  job_skills_extracted?: string[]
  job_skills_debug?: JobSkillsDebug | null
  score_breakdown?: ScoreBreakdown | null
  semantic_overlap?: number
  created_at: string
  job: Job | null
}

export interface DashboardStats {
  total_jobs: number
  matched_jobs: number
  avg_match_score: number
  top_missing_skills: string[]
  strongest_skills?: string[]
  top_companies?: CompanyMatchStat[]
  role_distribution?: CategoryMatchStat[]
  cv_profile_id: number | null
  demo_mode: boolean
}

export interface CompanyMatchStat {
  company: string
  count: number
  avg_score: number
}

export interface CategoryMatchStat {
  category: string
  count: number
  avg_score: number
}

export interface CVInsights {
  cv_profile_id: number | null
  strongest_skills: Array<{ skill: string; count: number; in_cv: boolean }>
  missing_high_value_skills: Array<{ skill: string; count: number; in_cv: boolean }>
  recommended_learning: string[]
  career_recommendations: string[]
}

export interface SavedJobEntry {
  id: number
  job_id: number
  created_at: string
  job: Job | null
}

export interface UserSettings {
  id: number
  email: string
  daily_digest_enabled: boolean
  digest_hour: number
  ui_language: string
  min_match_score: number
  preferred_job_keywords?: string[]
  last_digest_sent_at?: string | null
  demo_mode: boolean
  include_saved_jobs?: boolean
}

export interface EmailStatus {
  smtp_configured: boolean
  daily_email_enabled: boolean
  from_address: string
}

export interface EmailDigestResponse {
  sent: boolean
  message: string
  count: number
  preview?: string | null
  html_preview?: string | null
  preview_only?: boolean
  last_sent_at?: string | null
}

export interface EmailLogEntry {
  id: number
  recipient: string
  subject: string
  match_count: number
  sent: boolean
  preview_only: boolean
  error_message?: string | null
  created_at: string
}

export interface SchedulerLogEntry {
  id: number
  job_name: string
  status: string
  message: string
  match_count: number
  sent: boolean
  preview_only: boolean
  duration_ms?: number | null
  created_at: string
}

export interface CVUploadResponse {
  cv_profile: CVProfile
  matches: JobMatch[]
  total_jobs_scored: number
  extraction_method?: string
  skills_confidence?: SkillConfidence[]
  extraction_debug?: ExtractionDebug | null
  raw_text_preview?: string | null
  message: string
  partial_matches?: boolean
  match_warning?: string | null
  jobs_count?: number
  matches_created?: number
  top_score?: number | null
}

export interface HealthResponse {
  status: string
  app: string
  database?: string
  mock_mode?: boolean
}

export const liveApi = {
  health: () => request<HealthResponse>('/health'),

  getSettings: () => request<UserSettings>('/api/settings'),
  updateSettings: (data: Partial<UserSettings>) =>
    request<UserSettings>('/api/settings', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  getLatestCV: () => request<CVProfile | null>('/api/cv/latest'),

  /** Upload file → backend extracts skills + returns matched jobs */
  uploadCV: (file: File, signal?: AbortSignal) => {
    const form = new FormData()
    form.append('file', file)
    return request<CVUploadResponse>('/api/cv/upload', { method: 'POST', body: form, signal })
  },

  getMockJobs: (params?: Record<string, string>) => {
    const qs = params ? `?${new URLSearchParams(params)}` : ''
    return request<Job[]>(`/api/jobs/mock${qs}`)
  },

  getJobs: (params?: Record<string, string>) => {
    const qs = params ? `?${new URLSearchParams(params)}` : ''
    return request<Job[]>(`/api/jobs${qs}`)
  },

  refreshJobs: (sources = 'greenhouse,lever,remoteok') =>
    request<JobRefreshResponse>(`/api/jobs/refresh?sources=${encodeURIComponent(sources)}`, {
      method: 'POST',
    }),

  searchJobs: (params?: Record<string, string>) => {
    const qs = params ? `?${new URLSearchParams(params)}` : ''
    return request<JobSearchResponse>(`/api/jobs/search${qs}`)
  },
  getJob: (id: number) => request<Job>(`/api/jobs/${id}`),
  getCategories: () => request<string[]>('/api/jobs/categories'),

  getMatches: (cvId?: number, minScore = 0, israelOnly = true, sortBy = 'score') => {
    const params = new URLSearchParams()
    if (cvId) params.set('cv_profile_id', String(cvId))
    params.set('min_score', String(minScore))
    params.set('israel_only', String(israelOnly))
    params.set('sort_by', sortBy)
    params.set('limit', '100')
    return request<JobMatch[]>(`/api/matches?${params}`)
  },
  getMatch: (id: number) => request<JobMatch>(`/api/matches/${id}`),
  getDashboardStats: (cvId?: number, israelOnly = true) => {
    const params = new URLSearchParams()
    if (cvId) params.set('cv_profile_id', String(cvId))
    params.set('israel_only', String(israelOnly))
    return request<DashboardStats>(`/api/matches/stats/dashboard?${params}`)
  },

  activateDemo: () =>
    request<{
      cv_profile: CVProfile
      matches: JobMatch[]
      stats: DashboardStats
      message: string
    }>('/api/demo/activate', { method: 'POST' }),

  sendDigest: () =>
    request<EmailDigestResponse>('/api/email/daily', { method: 'POST' }),

  getEmailStatus: () => request<EmailStatus>('/api/email/status'),

  getEmailLogs: (limit = 10) =>
    request<EmailLogEntry[]>(`/api/email/logs?limit=${limit}`),

  getSchedulerLogs: (limit = 10) =>
    request<SchedulerLogEntry[]>(`/api/scheduler/logs?limit=${limit}`),

  getCVInsights: (cvId?: number, israelOnly = true) => {
    const params = new URLSearchParams()
    if (cvId) params.set('cv_profile_id', String(cvId))
    params.set('israel_only', String(israelOnly))
    return request<CVInsights>(`/api/cv/insights?${params}`)
  },

  getSavedJobs: () => request<SavedJobEntry[]>('/api/saved-jobs'),

  saveJob: (jobId: number) =>
    request<SavedJobEntry>(`/api/saved-jobs/${jobId}`, { method: 'POST' }),

  unsaveJob: (jobId: number) =>
    request<{ message: string }>(`/api/saved-jobs/${jobId}`, { method: 'DELETE' }),
}

/** @deprecated use liveApi — kept for imports */
export const api = liveApi
