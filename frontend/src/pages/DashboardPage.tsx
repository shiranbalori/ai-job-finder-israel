import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Briefcase,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
  Upload,
  User,
} from 'lucide-react'
import { isLiveFetchedJob, refreshJobs } from '../api'
import type { JobMatch } from '../api/client'
import { useApp } from '../context/AppContext'

import JobCard from '../components/JobCard'

import LoadingState from '../components/LoadingState'

import EmptyState from '../components/EmptyState'

import PageHeader from '../components/ui/PageHeader'

import StatCard from '../components/ui/StatCard'

import DemoModeButton from '../components/DemoModeButton'

import BackendStatus from '../components/BackendStatus'
import { pickTopSkillGap } from '../utils/text'

import DemoProfileCard from '../components/demo/DemoProfileCard'

import TopMatchHighlight from '../components/demo/TopMatchHighlight'

import DashboardAnalytics from '../components/dashboard/DashboardAnalytics'

import CVInsightsPanel from '../components/dashboard/CVInsightsPanel'

import SavedJobsSection from '../components/dashboard/SavedJobsSection'

import JobFiltersBar, {
  type JobFilterState,
  type SortOption,
} from '../components/dashboard/JobFiltersBar'



function extractCity(location: string): string {

  const part = location.split(/[,/·|]/)[0]?.trim()

  return part || location

}



function sortMatches(list: JobMatch[], sortBy: SortOption) {

  const copy = [...list]

  if (sortBy === 'newest') {

    return copy.sort(

      (a, b) =>

        new Date(b.job?.posted_at ?? 0).getTime() - new Date(a.job?.posted_at ?? 0).getTime(),

    )

  }

  if (sortBy === 'semantic') {

    return copy.sort(

      (a, b) =>

        (b.semantic_overlap ?? 0) - (a.semantic_overlap ?? 0) || b.match_score - a.match_score,

    )

  }

  return copy.sort((a, b) => b.match_score - a.match_score)

}



export default function DashboardPage() {

  const {

    t,

    cv,

    jobs,

    matches,

    stats,

    loading,

    demoMode,

    backendOnline,

    refresh,

    cvInsights,

    insightsLoading,

    savedJobIds,

  } = useApp()



  const [filters, setFilters] = useState<JobFilterState>({

    search: '',

    minScore: 0,

    category: '',

    company: '',

    city: '',

    workMode: '',

    sortBy: 'score',

    savedOnly: false,

  })

  const [fetchingJobs, setFetchingJobs] = useState(false)
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null)
  const [refreshMessageKind, setRefreshMessageKind] = useState<'success' | 'error' | 'info'>('info')
  const autoRefreshAttempted = useRef(false)

  const liveJobCount = useMemo(() => jobs.filter(isLiveFetchedJob).length, [jobs])

  const runJobRefresh = useCallback(
    async (options?: { silent?: boolean }) => {
      setFetchingJobs(true)
      if (!options?.silent) {
        setRefreshMessage(null)
      }
      try {
        const result = await refreshJobs()
        await refresh()
        const saved = result.total_created + result.total_updated
        if (saved === 0) {
          setRefreshMessage(t.dashboard.refreshEmpty)
          setRefreshMessageKind('info')
        } else {
          setRefreshMessage(
            result.message ?? `${t.dashboard.refreshDone} (${result.total_created} new)`,
          )
          setRefreshMessageKind('success')
        }
      } catch (err) {
        console.error('[Dashboard] job refresh failed:', err)
        setRefreshMessage(err instanceof Error ? err.message : t.dashboard.refreshError)
        setRefreshMessageKind('error')
      } finally {
        setFetchingJobs(false)
      }
    },
    [refresh, t.dashboard.refreshDone, t.dashboard.refreshEmpty, t.dashboard.refreshError],
  )

  useEffect(() => {
    if (
      demoMode ||
      loading ||
      fetchingJobs ||
      !backendOnline ||
      liveJobCount > 0 ||
      autoRefreshAttempted.current
    ) {
      return
    }
    autoRefreshAttempted.current = true
    void runJobRefresh({ silent: true })
  }, [demoMode, loading, fetchingJobs, backendOnline, liveJobCount, runJobRefresh])

  const refreshMessageStyles = {
    success:
      'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200',
    error:
      'border-rose-200 bg-rose-50 text-rose-900 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200',
    info: 'border-brand-100 bg-brand-50 text-brand-800 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-200',
  }[refreshMessageKind]



  const categories = useMemo(() => {

    const set = new Set(matches.map((m) => m.job?.category).filter(Boolean) as string[])

    return Array.from(set).sort()

  }, [matches])



  const companies = useMemo(() => {

    const set = new Set(matches.map((m) => m.job?.company).filter(Boolean) as string[])

    return Array.from(set).sort()

  }, [matches])



  const cities = useMemo(() => {

    const set = new Set(

      matches.map((m) => (m.job?.location ? extractCity(m.job.location) : '')).filter(Boolean),

    )

    return Array.from(set).sort()

  }, [matches])



  const filtered = useMemo(() => {

    const list = matches.filter((m) => {

      const job = m.job

      if (!job) return false

      if (m.match_score < filters.minScore) return false

      if (filters.category && job.category !== filters.category) return false

      if (filters.company && job.company !== filters.company) return false

      if (filters.city && extractCity(job.location) !== filters.city) return false

      if (filters.workMode && job.work_mode !== filters.workMode) return false

      if (filters.savedOnly && !savedJobIds.has(job.id)) return false

      if (filters.search) {

        const q = filters.search.toLowerCase()

        if (!`${job.title} ${job.company} ${job.location}`.toLowerCase().includes(q)) return false

      }

      return true

    })

    return sortMatches(list, filters.sortBy)

  }, [matches, filters, savedJobIds])



  const handleRefreshJobs = () => {
    void runJobRefresh()
  }



  const patchFilters = (patch: Partial<JobFilterState>) =>

    setFilters((prev) => ({ ...prev, ...patch }))



  if (loading) return <LoadingState variant="dashboard" />



  return (

    <div className="page-container">

      <PageHeader

        title={t.dashboard.title}

        subtitle={t.dashboard.subtitle}

        badge={demoMode ? 'Demo Mode' : undefined}

      >

        <BackendStatus />

        {!demoMode && (

          <button

            type="button"

            className="btn-secondary btn-sm inline-flex items-center gap-2"

            onClick={handleRefreshJobs}

            disabled={fetchingJobs}

          >

            <RefreshCw className={`h-4 w-4 ${fetchingJobs ? 'animate-spin' : ''}`} />

            {fetchingJobs ? t.dashboard.refreshingJobs : t.dashboard.refreshJobs}

          </button>

        )}

        <DemoModeButton />

      </PageHeader>



      {!demoMode && (fetchingJobs || refreshMessage) && (
        <div className="mb-6 space-y-3">
          {fetchingJobs && (
            <p
              className="rounded-xl border border-brand-100 bg-brand-50 px-4 py-3 text-sm text-brand-800 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-200"
              role="status"
            >
              {t.dashboard.refreshingJobs}
            </p>
          )}
          {refreshMessage && !fetchingJobs && (
            <p className={`rounded-xl border px-4 py-3 text-sm ${refreshMessageStyles}`} role="status">
              {refreshMessage}
            </p>
          )}
        </div>
      )}



      {stats && (

        <div className="stagger mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <StatCard label={t.dashboard.totalJobs} value={jobs.length || stats.total_jobs} icon={Briefcase} accent="brand" />

          <StatCard label={t.dashboard.matched} value={stats.matched_jobs} icon={Target} accent="violet" trend={demoMode ? t.dashboard.demoTrend : undefined} />

          <StatCard label={t.dashboard.avgScore} value={`${stats.avg_match_score}%`} icon={TrendingUp} accent="emerald" />

          <StatCard label={t.dashboard.topGaps} value={pickTopSkillGap(stats.top_missing_skills)} icon={Sparkles} accent="amber" />

        </div>

      )}



      {!cv ? (

        <EmptyState

          title={t.dashboard.noCv}

          description={t.landing.demoHint}

          action={

            <>

              <DemoModeButton size="large" />

              <Link to="/upload" className="btn-secondary">
                <Upload className="h-4 w-4" />
                {t.landing.ctaUpload}
              </Link>

            </>

          }

        />

      ) : (

        <div className="section-gap animate-fade-in">

          {stats && (stats.strongest_skills?.length || stats.top_companies?.length) ? (

            <DashboardAnalytics stats={stats} />

          ) : null}



          <CVInsightsPanel insights={cvInsights} loading={insightsLoading} />



          <section>

            {demoMode ? (

              <DemoProfileCard cv={cv} />

            ) : (

              <div className="card overflow-hidden p-0">

                <div className="bg-gradient-to-r from-brand-50/50 to-white px-6 py-5 dark:from-brand-950/30 dark:to-slate-800 lg:px-8 lg:py-6">

                  <div className="flex items-start gap-4">

                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-brand text-xl font-bold text-white shadow-soft">

                      {cv.full_name?.charAt(0) ?? <User className="h-6 w-6" />}

                    </div>

                    <div>

                      <p className="text-overline uppercase text-brand-600 dark:text-brand-400">{t.dashboard.activeProfile}</p>

                      <h2 className="mt-1 text-xl font-bold text-slate-900 dark:text-slate-100">{cv.full_name}</h2>

                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">

                        {cv.years_experience}+ {t.dashboard.yearsLabel} · {cv.job_titles[0]}

                      </p>

                      <div className="mt-3 flex flex-wrap gap-1.5">

                        {cv.skills.slice(0, 6).map((s) => (

                          <span key={s} className="badge bg-white text-slate-700 ring-1 ring-slate-200/80 dark:bg-slate-700 dark:text-slate-200 dark:ring-slate-600">

                            {s}

                          </span>

                        ))}

                      </div>

                    </div>

                  </div>

                </div>

              </div>

            )}

          </section>



          {demoMode && matches[0] && (

            <section>

              <TopMatchHighlight match={matches[0]} />

            </section>

          )}



          <SavedJobsSection
            matches={matches}
            onShowSavedOnly={() => patchFilters({ savedOnly: true })}
          />

          <div className="grid gap-6 xl:grid-cols-[minmax(280px,320px)_1fr] xl:gap-8">

            <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">

              {!demoMode && (
                <div className="card p-5">
                  <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
                    <Briefcase className="h-4 w-4 text-brand-500" />
                    {t.dashboard.jobsFromBackend}
                    <span className="badge-brand ms-auto">{jobs.length}</span>
                  </h2>
                  <p className="text-caption text-slate-500">
                    {fetchingJobs ? t.dashboard.refreshingJobs : `${liveJobCount} ${t.dashboard.liveJobsCount}`}
                  </p>
                </div>
              )}

              <JobFiltersBar

                filters={filters}

                onChange={patchFilters}

                categories={categories}

                companies={companies}

                cities={cities}

                resultCount={filtered.length}

              />

            </aside>



            <section>

              <div className="mb-5 flex flex-wrap items-center justify-between gap-2">

                <p className="text-sm text-slate-600 dark:text-slate-400">

                  <span className="font-semibold text-slate-900 dark:text-slate-100">{filtered.length}</span>{' '}

                  {t.dashboard.resultsLabel}

                </p>

              </div>



              {filtered.length === 0 ? (

                <EmptyState variant="compact" title={t.empty.matches} description={t.empty.jobs} />

              ) : (

                <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-2">

                  {filtered.map((m, i) => (
                    <JobCard key={m.id} match={m} index={i} />
                  ))}

                </div>

              )}

            </section>

          </div>

        </div>

      )}

    </div>

  )

}

