import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  Building2,
  Calendar,
  Clock,
  ExternalLink,
  MapPin,
  SearchX,
  Wallet,
} from 'lucide-react'
import { api, type Job, type JobMatch } from '../api'
import { useApp } from '../context/AppContext'
import MatchScoreRing from '../components/MatchScoreRing'
import LoadingState from '../components/LoadingState'
import EmptyState from '../components/EmptyState'
import PageHeader from '../components/ui/PageHeader'
import JobSourceBadge from '../components/JobSourceBadge'
import JobLocationBadge from '../components/JobLocationBadge'
import MatchInsightPanel from '../components/MatchInsightPanel'
import SaveJobButton from '../components/SaveJobButton'

export default function JobDetailsPage() {
  const { id } = useParams()
  const { t, matches, cv } = useApp()
  const [job, setJob] = useState<Job | null>(null)
  const [match, setMatch] = useState<JobMatch | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const jobId = Number(id)
    if (!jobId) return

    const existing = matches.find((m) => m.job_id === jobId)
    if (existing?.job) {
      setMatch(existing)
      setJob(existing.job)
      setLoading(false)
      return
    }

    Promise.all([api.getJob(jobId), cv ? api.getMatches(cv.id, 0) : Promise.resolve([])])
      .then(([j, allMatches]) => {
        setJob(j)
        setMatch(allMatches.find((m) => m.job_id === jobId) ?? null)
      })
      .finally(() => setLoading(false))
  }, [id, matches, cv])

  if (loading) return <LoadingState message={t.job.loadingDetails} />

  if (!job) {
    return (
      <div className="page-container">
        <EmptyState
          icon={SearchX}
          title={t.job.notFound}
          description={t.job.notFoundDesc}
          action={
            <Link to="/dashboard" className="btn-primary">
              {t.job.back}
            </Link>
          }
        />
      </div>
    )
  }

  const scoreLabel =
    match && match.match_score >= 85
      ? t.job.excellentFit
      : match && match.match_score >= 70
        ? t.job.goodFit
        : t.job.partialFit

  return (
    <div className="page-container animate-slide-up">
      <Link
        to="/dashboard"
        className="mb-8 inline-flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-brand-600 transition hover:bg-brand-50"
      >
        <ArrowLeft className="h-4 w-4" />
        {t.job.back}
      </Link>

      <PageHeader title={job.title} subtitle={`${job.company} · ${job.location}`}>
        <SaveJobButton jobId={job.id} showLabel />
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-3 lg:gap-8">
        <div className="lg:col-span-2">
          <div className="card space-y-8 p-6 lg:p-8">
            <div>
              <div className="flex flex-wrap gap-2">
                <JobSourceBadge job={job} />
                <JobLocationBadge job={job} />
                <span className="badge-brand">{job.category}</span>
                <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                  {job.employment_type}
                </span>
                {job.language === 'he' && (
                  <span className="badge bg-blue-50 text-blue-700 ring-1 ring-blue-100">עברית</span>
                )}
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
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
            </div>

            <hr className="border-slate-100" />

            <section>
              <h2 className="text-heading font-semibold text-slate-900">{t.job.description}</h2>
              <p className="mt-3 text-body-lg leading-relaxed text-slate-600">{job.description}</p>
            </section>

            <section>
              <h2 className="text-heading font-semibold text-slate-900">{t.job.requirements}</h2>
              <ul className="mt-4 space-y-2.5">
                {job.requirements.map((r) => (
                  <li key={r} className="flex items-start gap-3 text-sm text-slate-600">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                    {r}
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h2 className="text-heading font-semibold text-slate-900">{t.job.techStack}</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {job.skills.map((s) => (
                  <span key={s} className="badge bg-slate-100 text-slate-700 ring-1 ring-slate-200">
                    {s}
                  </span>
                ))}
              </div>
            </section>

            {job.url && (
              <a
                href={job.url}
                target="_blank"
                rel="noreferrer"
                className="btn-primary inline-flex w-full sm:w-auto"
              >
                {t.job.apply}
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>

        <div className="space-y-6">
          {match ? (
            <div className="card sticky top-24 border-brand-100/80 bg-gradient-to-b from-brand-50/40 to-white p-6">
              <div className="flex flex-col items-center text-center">
                <MatchScoreRing score={match.match_score} size="lg" />
                <p className="mt-3 text-overline uppercase text-slate-500">{t.job.matchScore}</p>
              </div>
              <div className="mt-6">
                <MatchInsightPanel match={match} scoreLabel={scoreLabel} compact />
              </div>
              <p className="mt-6 flex items-center gap-2 text-caption text-slate-400">
                <Clock className="h-3.5 w-3.5" />
                {new Date(match.created_at).toLocaleDateString()}
              </p>
            </div>
          ) : (
            <div className="card p-6 text-center">
              <p className="text-sm text-slate-500">{t.dashboard.noCv}</p>
              <Link to="/upload" className="btn-secondary btn-sm mt-4 inline-flex">
                {t.landing.ctaUpload}
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
