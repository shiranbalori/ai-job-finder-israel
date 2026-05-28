import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Building2, Calendar, ExternalLink, MapPin, Wallet, X } from 'lucide-react'
import type { Job, JobMatch } from '../api/client'
import { useApp } from '../context/AppContext'
import MatchScoreRing from './MatchScoreRing'
import JobSourceBadge from './JobSourceBadge'
import JobLocationBadge from './JobLocationBadge'
import MatchInsightPanel from './MatchInsightPanel'

interface Props {
  job: Job
  match: JobMatch | null
  open: boolean
  onClose: () => void
}

export default function JobDetailsModal({ job, match, open, onClose }: Props) {
  const { t } = useApp()

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  const scoreLabel =
    match && match.match_score >= 85
      ? t.job.excellentFit
      : match && match.match_score >= 70
        ? t.job.goodFit
        : t.job.partialFit

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        aria-label="Close"
        onClick={onClose}
      />
      <div className="relative flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:rounded-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4 sm:px-6">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap gap-1.5">
              <JobSourceBadge job={job} />
              <JobLocationBadge job={job} />
              <span className="badge-brand">{job.category}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">{job.title}</h2>
            <p className="mt-1 text-sm text-slate-600">
              {job.company} · {job.location}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="grid flex-1 gap-0 overflow-y-auto lg:grid-cols-5">
          <div className="space-y-6 border-b border-slate-100 p-5 sm:p-6 lg:col-span-3 lg:border-b-0 lg:border-e">
            <div className="grid gap-2 sm:grid-cols-2">
              <p className="flex items-center gap-2 text-sm text-slate-600">
                <Building2 className="h-4 w-4 shrink-0 text-brand-500" />
                {job.company}
              </p>
              <p className="flex items-center gap-2 text-sm text-slate-600">
                <MapPin className="h-4 w-4 shrink-0 text-brand-500" />
                {job.location}
              </p>
              {job.salary_range && (
                <p className="flex items-center gap-2 text-sm font-semibold text-violet-600">
                  <Wallet className="h-4 w-4 shrink-0" />
                  {job.salary_range}
                </p>
              )}
              <p className="flex items-center gap-2 text-sm text-slate-500">
                <Calendar className="h-4 w-4 shrink-0 text-slate-400" />
                {new Date(job.posted_at).toLocaleDateString()}
              </p>
            </div>

            <section>
              <h3 className="text-sm font-semibold text-slate-900">{t.job.description}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{job.description}</p>
            </section>

            <section>
              <h3 className="text-sm font-semibold text-slate-900">{t.job.techStack}</h3>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {job.skills.map((s) => (
                  <span key={s} className="badge bg-slate-100 text-slate-700 ring-1 ring-slate-200">
                    {s}
                  </span>
                ))}
              </div>
            </section>

            {job.url && (
              <a href={job.url} target="_blank" rel="noreferrer" className="btn-primary inline-flex">
                {t.job.apply}
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>

          <div className="bg-gradient-to-b from-brand-50/30 to-white p-5 sm:p-6 lg:col-span-2">
            {match ? (
              <div className="space-y-5">
                <div className="flex flex-col items-center">
                  <MatchScoreRing score={match.match_score} size="lg" />
                  <p className="mt-2 text-overline uppercase text-slate-500">{t.job.matchScore}</p>
                </div>
                <MatchInsightPanel match={match} scoreLabel={scoreLabel} compact />
              </div>
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-slate-500">{t.dashboard.noCv}</p>
                <Link to="/upload" className="btn-secondary btn-sm mt-4 inline-flex" onClick={onClose}>
                  {t.landing.ctaUpload}
                </Link>
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-slate-100 px-5 py-3 sm:px-6">
          <Link
            to={`/jobs/${job.id}`}
            className="text-sm font-medium text-brand-600 hover:text-brand-700"
            onClick={onClose}
          >
            {t.job.openFullPage}
          </Link>
        </div>
      </div>
    </div>
  )
}
