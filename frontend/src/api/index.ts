/**
 * API facade — connects to FastAPI backend by default.
 * Set VITE_USE_MOCK=true in .env to use offline mock data only.
 */

import { liveApi } from './client'
import { mockApi } from '../mock/mockApi'

export type {
  CVProfile,
  Job,
  JobMatch,
  DashboardStats,
  UserSettings,
  CVUploadResponse,
  HealthResponse,
  SkillConfidence,
  ExtractionDebug,
  ScoreBreakdown,
} from './client'

export { uploadRealCV, validateCVFile, CVUploadError } from './cvService'
export { refreshJobs, searchJobs, JobFetchError } from './jobService'
export { getJobSourceKind, isLiveFetchedJob, getLocationTag, isIsraeliJob } from './jobHelpers'
export type { JobSourceKind, LocationTag } from './jobHelpers'

/** True only when explicitly enabled — live backend is the default for step 4. */
export const USE_MOCK =
  import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === '1'

async function withFallback<T>(live: () => Promise<T>, mock: () => Promise<T>): Promise<T> {
  if (USE_MOCK) return mock()
  try {
    return await live()
  } catch (err) {
    console.warn('[API] Live backend failed, falling back to mock:', err)
    return mock()
  }
}

/** Real Mode — never fall back to mock (upload must hit the backend). */
async function liveOnly<T>(live: () => Promise<T>): Promise<T> {
  if (USE_MOCK) {
    throw new Error('Real upload requires VITE_USE_MOCK=false and a running backend.')
  }
  return live()
}

export const api = {
  health: () => withFallback(() => liveApi.health(), () => mockApi.health()),
  getSettings: () => withFallback(() => liveApi.getSettings(), () => mockApi.getSettings()),
  updateSettings: (d: Parameters<typeof liveApi.updateSettings>[0]) =>
    withFallback(() => liveApi.updateSettings(d), () => mockApi.updateSettings(d)),
  getLatestCV: () => withFallback(() => liveApi.getLatestCV(), () => mockApi.getLatestCV()),
  uploadCV: (f: File) => liveOnly(() => liveApi.uploadCV(f)),
  getMockJobs: (p?: Record<string, string>) =>
    withFallback(() => liveApi.getMockJobs(p), () => mockApi.getJobs(p)),
  getJobs: (p?: Record<string, string>) =>
    withFallback(() => liveApi.getJobs(p), () => mockApi.getJobs(p)),
  refreshJobs: (sources?: string[]) =>
    liveOnly(() => liveApi.refreshJobs(sources?.join(',') ?? 'greenhouse,lever,remoteok')),
  searchJobs: (p?: Record<string, string>) =>
    withFallback(() => liveApi.searchJobs(p), () =>
      mockApi.getJobs(p).then((items) => ({ items, total: items.length, query: p?.q ?? null })),
    ),
  getJob: (id: number) => withFallback(() => liveApi.getJob(id), () => mockApi.getJob(id)),
  getCategories: () => withFallback(() => liveApi.getCategories(), () => mockApi.getCategories()),
  getMatches: (cvId?: number, min?: number, israelOnly = true, sortBy = 'score') =>
    withFallback(
      () => liveApi.getMatches(cvId, min, israelOnly, sortBy),
      () => mockApi.getMatches(cvId, min),
    ),
  getMatch: (id: number) => withFallback(() => liveApi.getMatch(id), () => mockApi.getMatch(id)),
  getDashboardStats: (cvId?: number, israelOnly = true) =>
    withFallback(
      () => liveApi.getDashboardStats(cvId, israelOnly),
      () => mockApi.getDashboardStats(cvId),
    ),
  activateDemo: () => withFallback(() => liveApi.activateDemo(), () => mockApi.activateDemo()),
  sendDigest: () => withFallback(() => liveApi.sendDigest(), () => mockApi.sendDigest()),
  getEmailStatus: () =>
    withFallback(() => liveApi.getEmailStatus(), () => mockApi.getEmailStatus()),
  getEmailLogs: (limit?: number) =>
    withFallback(() => liveApi.getEmailLogs(limit), () => mockApi.getEmailLogs(limit)),
  getSchedulerLogs: (limit?: number) =>
    withFallback(() => liveApi.getSchedulerLogs(limit), () => mockApi.getSchedulerLogs(limit)),
  getCVInsights: (cvId?: number, israelOnly = true) =>
    withFallback(
      () => liveApi.getCVInsights(cvId, israelOnly),
      () => mockApi.getCVInsights(cvId),
    ),
  getSavedJobs: () => withFallback(() => liveApi.getSavedJobs(), () => mockApi.getSavedJobs()),
  saveJob: (jobId: number) =>
    withFallback(() => liveApi.saveJob(jobId), () => mockApi.saveJob(jobId)),
  unsaveJob: (jobId: number) =>
    withFallback(() => liveApi.unsaveJob(jobId), () => mockApi.unsaveJob(jobId)),
  getCompanies: () => mockApi.getCompanies(),
}

/** Ping backend — used for connection banner */
export async function checkBackendHealth(): Promise<{ ok: boolean; mock: boolean }> {
  if (USE_MOCK) return { ok: true, mock: true }
  try {
    const h = await liveApi.health()
    return { ok: h.status === 'ok' || h.status === 'degraded', mock: false }
  } catch {
    return { ok: false, mock: false }
  }
}
