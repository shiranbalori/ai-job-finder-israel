import { getJobSourceKind } from '../api/jobHelpers'
import type { Job } from '../api/client'
import { useApp } from '../context/AppContext'

interface Props {
  job: Pick<Job, 'is_demo' | 'source' | 'work_mode'>
  className?: string
}

export default function JobSourceBadge({ job, className = '' }: Props) {
  const { t } = useApp()
  const kind = getJobSourceKind(job)

  if (kind === 'demo') {
    return (
      <span
        className={`badge bg-amber-50 text-amber-800 ring-1 ring-amber-200 ${className}`}
        title={t.job.sourceDemoHint}
      >
        {t.job.sourceDemo}
      </span>
    )
  }

  const sourceLabel =
    kind === 'greenhouse'
      ? t.job.sourceGreenhouse
      : kind === 'lever'
        ? t.job.sourceLever
        : kind === 'remoteok'
          ? t.job.sourceRemoteOK
          : job.source

  return (
    <span
      className={`badge bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200 ${className}`}
      title={t.job.sourceLiveHint}
    >
      {t.job.sourceLive}
      {sourceLabel ? ` · ${sourceLabel}` : ''}
    </span>
  )
}
