import { Link } from 'react-router-dom'
import { Bookmark, Star } from 'lucide-react'
import type { JobMatch } from '../../api/client'
import { useApp } from '../../context/AppContext'
import SaveJobButton from '../SaveJobButton'
import MatchScoreRing from '../MatchScoreRing'
import CompanyLogo from '../CompanyLogo'

interface Props {
  matches: JobMatch[]
  onShowSavedOnly: () => void
}

export default function SavedJobsSection({ matches, onShowSavedOnly }: Props) {
  const { savedJobIds, t } = useApp()

  const savedMatches = matches
    .filter((m) => m.job && savedJobIds.has(m.job_id))
    .sort((a, b) => b.match_score - a.match_score)

  if (savedMatches.length === 0) return null

  return (
    <section className="card overflow-hidden p-0">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-gradient-to-r from-amber-50/80 to-white px-5 py-4 dark:border-slate-700 dark:from-amber-950/30 dark:to-slate-800 lg:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400">
            <Bookmark className="h-5 w-5 fill-current" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              {t.dashboard.savedJobsTitle}
            </h2>
            <p className="text-caption text-slate-500 dark:text-slate-400">
              {savedMatches.length} {t.dashboard.savedJobsCount}
            </p>
          </div>
        </div>
        <button type="button" className="btn-secondary btn-sm" onClick={onShowSavedOnly}>
          <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-500" />
          {t.dashboard.viewSavedOnly}
        </button>
      </div>

      <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 lg:p-5">
        {savedMatches.slice(0, 6).map((m) => {
          const job = m.job!
          return (
            <div
              key={m.id}
              className="flex items-start gap-3 rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 transition hover:border-amber-200 hover:shadow-sm dark:border-slate-600 dark:bg-slate-800/50 dark:hover:border-amber-800"
            >
              <CompanyLogo company={job.company} size="sm" />
              <div className="min-w-0 flex-1">
                <Link
                  to={`/jobs/${m.job_id}`}
                  className="line-clamp-2 text-sm font-semibold text-slate-900 hover:text-brand-600 dark:text-slate-100 dark:hover:text-brand-400"
                >
                  {job.title}
                </Link>
                <p className="mt-0.5 truncate text-caption text-slate-500 dark:text-slate-400">
                  {job.company}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <MatchScoreRing score={m.match_score} size="sm" />
                  <SaveJobButton jobId={job.id} />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
