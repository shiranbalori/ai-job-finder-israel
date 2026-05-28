/**
 * Job API service — fetch real jobs from Greenhouse/Lever via backend.
 */

import { liveApi, type JobRefreshResponse, type JobSearchResponse } from './client'
import { checkBackendHealth, USE_MOCK } from './index'

export type { JobRefreshResponse, JobSearchResponse }

export class JobFetchError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'JobFetchError'
  }
}

export async function refreshJobs(
  sources: string[] = ['greenhouse', 'lever', 'remoteok'],
): Promise<JobRefreshResponse> {
  if (USE_MOCK) {
    throw new JobFetchError('Job refresh requires VITE_USE_MOCK=false and a running backend.')
  }
  const health = await checkBackendHealth()
  if (!health.ok) {
    throw new JobFetchError('Backend offline — start FastAPI before refreshing jobs.')
  }
  return liveApi.refreshJobs(sources)
}

export async function searchJobs(params?: {
  q?: string
  category?: string
  work_mode?: string
  source?: string
  include_demo?: boolean
  demo_only?: boolean
}): Promise<JobSearchResponse> {
  return liveApi.searchJobs(params)
}
