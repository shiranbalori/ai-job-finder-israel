import { getLocationTag } from '../api/jobHelpers'
import type { Job } from '../api/client'
import { useApp } from '../context/AppContext'

interface Props {
  job: Pick<Job, 'location_tag' | 'location' | 'is_israel'>
  className?: string
}

export default function JobLocationBadge({ job, className = '' }: Props) {
  const { t } = useApp()
  const tag = getLocationTag(job)

  const styles: Record<string, string> = {
    israel: 'bg-blue-50 text-blue-800 ring-blue-200',
    remote_israel: 'bg-violet-50 text-violet-800 ring-violet-200',
    hybrid: 'bg-teal-50 text-teal-800 ring-teal-200',
  }

  const labels: Record<string, string> = {
    israel: t.job.locationIsrael,
    remote_israel: t.job.locationRemoteIsrael,
    hybrid: t.job.locationHybrid,
  }

  return (
    <span className={`badge ring-1 ${styles[tag]} ${className}`}>{labels[tag]}</span>
  )
}
