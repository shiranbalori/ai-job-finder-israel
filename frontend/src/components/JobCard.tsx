import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowUpRight,
  ChevronDown,
  ExternalLink,
  Eye,
  MapPin,
} from 'lucide-react'
import type { JobMatch } from '../api/client'
import MatchScoreRing from './MatchScoreRing'
import JobSourceBadge from './JobSourceBadge'
import JobLocationBadge from './JobLocationBadge'
import JobDetailsModal from './JobDetailsModal'
import CompanyLogo from './CompanyLogo'
import SaveJobButton from './SaveJobButton'
import { useApp } from '../context/AppContext'

interface Props {
  match: JobMatch
  index?: number
}

export default function JobCard({ match, index = 0 }: Props) {
  const { t } = useApp()
  const job = match.job
  const [modalOpen, setModalOpen] = useState(false)
  const [expanded, setExpanded] = useState(false)

  if (!job) return null

  const scoreTier =
    match.match_score >= 85 ? 'high' : match.match_score >= 70 ? 'good' : 'fair'

  return (
    <>
      <article
        className="card-interactive group relative flex flex-col overflow-hidden p-0 transition-all duration-300 hover:-translate-y-0.5"
        style={{ animationDelay: `${index * 0.04}s` }}
      >
        <div
          className={`h-1 w-full ${
            scoreTier === 'high'
              ? 'bg-gradient-to-r from-emerald-400 to-emerald-500'
              : scoreTier === 'good'
                ? 'bg-gradient-to-r from-brand-400 to-brand-500'
                : 'bg-gradient-to-r from-slate-300 to-slate-400 dark:from-slate-600 dark:to-slate-500'
          }`}
        />

        {/* Always-visible save — top-right */}
        <div className="absolute end-3 top-3 z-10">
          <SaveJobButton jobId={job.id} />
        </div>

        <div className="flex flex-1 flex-col p-5 pe-14 lg:p-6 lg:pe-16">
          <div className="flex items-start gap-3">
            <CompanyLogo company={job.company} size="md" />
            <div className="min-w-0 flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-1.5">
                <JobSourceBadge job={job} />
                <JobLocationBadge job={job} />
                <span className="badge-brand">{job.category}</span>
                {match.match_score >= 85 && <span className="badge-success">Top match</span>}
              </div>
              <Link to={`/jobs/${match.job_id}`}>
                <h3 className="text-heading font-semibold text-slate-900 transition group-hover:text-brand-600 dark:text-slate-100 dark:group-hover:text-brand-400">
                  {job.title}
                </h3>
              </Link>
              <p className="mt-1 truncate text-sm font-medium text-slate-600 dark:text-slate-300">
                {job.company}
              </p>
              <p className="mt-0.5 flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
                <MapPin className="h-3.5 w-3.5 shrink-0" />
                {job.location}
              </p>
            </div>
            <div className="shrink-0">
              <MatchScoreRing score={match.match_score} size="md" />
            </div>
          </div>

          {job.salary_range && (
            <p className="mt-3 text-sm font-semibold text-violet-600 dark:text-violet-400">
              {job.salary_range}
            </p>
          )}

          <button
            type="button"
            className="mt-4 flex w-full items-center justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50/80 px-3 py-2.5 text-start text-sm transition hover:border-brand-200 hover:bg-brand-50/50 dark:border-slate-700 dark:bg-slate-800/50 dark:hover:border-brand-800"
            onClick={() => setExpanded(!expanded)}
          >
            <span className="font-medium text-slate-700 dark:text-slate-200">
              {t.dashboard.matchExplanation}
            </span>
            <ChevronDown
              className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            />
          </button>

          {expanded && (
            <div className="mt-2 animate-fade-in space-y-2 rounded-xl border border-slate-100 bg-white p-3 text-sm leading-relaxed text-slate-600 dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-300">
              <p>{match.match_reason}</p>
              {match.semantic_overlap != null && match.semantic_overlap > 0 && (
                <p className="text-xs font-medium text-brand-600 dark:text-brand-400">
                  {t.job.semanticOverlap} {Math.round(match.semantic_overlap * 100)}%
                </p>
              )}
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-1.5 border-t border-slate-100 pt-4 dark:border-slate-700">
            {match.matched_skills.slice(0, 4).map((s) => (
              <span key={s} className="badge-success text-[11px]">
                {s}
              </span>
            ))}
            {match.missing_skills.slice(0, 3).map((s) => (
              <span key={s} className="badge-warning text-[11px]">
                − {s}
              </span>
            ))}
          </div>

          <div className="mt-4 flex gap-2">
            {job.url ? (
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary btn-sm inline-flex flex-1 items-center justify-center gap-1.5"
              >
                {t.dashboard.applyNow}
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            ) : (
              <Link
                to={`/jobs/${match.job_id}`}
                className="btn-primary btn-sm inline-flex flex-1 items-center justify-center gap-1.5"
              >
                {t.dashboard.applyNow}
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            )}
            <SaveJobButton jobId={job.id} showLabel />
            <button
              type="button"
              className="btn-secondary btn-sm inline-flex items-center justify-center gap-1.5 px-3"
              onClick={() => setModalOpen(true)}
            >
              <Eye className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{t.job.quickView}</span>
            </button>
          </div>
        </div>
      </article>

      <JobDetailsModal
        job={job}
        match={match}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </>
  )
}
