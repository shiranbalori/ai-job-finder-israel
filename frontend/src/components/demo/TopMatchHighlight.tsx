import { Link } from 'react-router-dom'
import { ArrowUpRight, Trophy } from 'lucide-react'
import type { JobMatch } from '../../api/client'
import MatchScoreRing from '../MatchScoreRing'
import SaveJobButton from '../SaveJobButton'
import { useApp } from '../../context/AppContext'

interface Props {
  match: JobMatch
}

/** Highlight card for #1 demo match — interview-ready hero element. */
export default function TopMatchHighlight({ match }: Props) {
  const { t } = useApp()
  const job = match.job
  if (!job) return null

  return (
    <div className="card-interactive group relative block overflow-hidden border-emerald-200/80 bg-gradient-to-br from-emerald-50/60 via-white to-white p-0 dark:border-emerald-900/50 dark:from-emerald-950/30 dark:via-slate-800 dark:to-slate-800">
      <div className="absolute end-3 top-3 z-10">
        <SaveJobButton jobId={job.id} />
      </div>
      <Link
        to={`/jobs/${match.job_id}`}
        className="block"
      >
      <div className="h-1 bg-gradient-to-r from-emerald-400 to-emerald-500" />
      <div className="p-6 lg:p-8">
        <div className="mb-4 flex items-center gap-2 text-emerald-700">
          <Trophy className="h-5 w-5" />
          <span className="text-overline uppercase">{t.demo.topMatch}</span>
          <ArrowUpRight className="ms-auto h-4 w-4 text-slate-300 transition group-hover:text-brand-500" />
        </div>
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="text-xl font-bold text-slate-900 transition group-hover:text-brand-600">
              {job.title}
            </h3>
            <p className="mt-1 text-sm text-slate-600">
              {job.company} · {job.location}
            </p>
            {job.salary_range && (
              <p className="mt-1 text-sm font-semibold text-violet-600">{job.salary_range}</p>
            )}
            <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-slate-600">
              {match.match_reason}
            </p>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {match.matched_skills.slice(0, 5).map((s) => (
                <span key={s} className="badge-success">
                  ✓ {s}
                </span>
              ))}
              {match.missing_skills[0] && (
                <span className="badge-warning">+ {match.missing_skills[0]}</span>
              )}
            </div>
          </div>
          <MatchScoreRing score={match.match_score} size="lg" />
        </div>
      </div>
      </Link>
    </div>
  )
}
