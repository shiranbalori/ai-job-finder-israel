/** Job source + Israel location helpers. */

import type { Job } from './client'

export type JobSourceKind = 'demo' | 'greenhouse' | 'lever' | 'remoteok' | 'other'
export type LocationTag = 'israel' | 'remote_israel' | 'hybrid'

export function getJobSourceKind(job: Pick<Job, 'is_demo' | 'source'>): JobSourceKind {
  if (job.is_demo || job.source === 'seed') return 'demo'
  if (job.source === 'greenhouse') return 'greenhouse'
  if (job.source === 'lever') return 'lever'
  if (job.source === 'remoteok') return 'remoteok'
  return 'other'
}

export function isLiveFetchedJob(job: Pick<Job, 'is_demo' | 'source'>): boolean {
  return !job.is_demo && job.source !== 'seed'
}

export function getLocationTag(job: Pick<Job, 'location_tag' | 'location' | 'is_israel'>): LocationTag {
  if (job.location_tag === 'remote_israel' || job.location_tag === 'hybrid') {
    return job.location_tag
  }
  const loc = (job.location || '').toLowerCase()
  if (loc.includes('hybrid')) return 'hybrid'
  if (loc.includes('remote') && loc.includes('israel')) return 'remote_israel'
  return 'israel'
}

export function isIsraeliJob(job: Pick<Job, 'is_israel' | 'is_demo'>): boolean {
  return job.is_israel !== false || job.is_demo
}
