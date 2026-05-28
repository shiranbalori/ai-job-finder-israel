import { useState } from 'react'

import { Link } from 'react-router-dom'

import { AlertCircle, ArrowRight, CheckCircle2, ChevronDown, ChevronUp, User } from 'lucide-react'

import type { CVProfile, JobMatch, SkillConfidence } from '../api/client'

import MatchScoreRing from './MatchScoreRing'

import MatchInsightPanel, { SkillConfidenceList } from './MatchInsightPanel'

import ExtractionDebugPanel from './ExtractionDebugPanel'

import SaveJobButton from './SaveJobButton'

import type { CVUploadResponse, ExtractionDebug } from '../api/client'

import { useApp } from '../context/AppContext'



interface Props {

  cv: CVProfile

  matches: JobMatch[]

  rawTextPreview?: string | null

  extractionMethod?: string

  skillsConfidence?: SkillConfidence[]

  extractionDebug?: ExtractionDebug | null

  uploadResponse?: CVUploadResponse

  message?: string

  matchWarning?: string | null

  partialMatches?: boolean

  matchesCreated?: number

  jobsCount?: number

  topScore?: number | null

}



/** Shows extracted profile and top matches after a real backend upload. */

export default function UploadResults({

  cv,

  matches,

  rawTextPreview,

  extractionMethod,

  skillsConfidence,

  extractionDebug,

  uploadResponse,

  message,

  matchWarning,

  partialMatches,

  matchesCreated,

  jobsCount,

  topScore,

}: Props) {

  const { t } = useApp()

  const [showRawText, setShowRawText] = useState(false)

  const sorted = [...matches].sort((a, b) => b.match_score - a.match_score)

  const top = sorted.slice(0, 10)

  const hasMatches = sorted.length > 0



  const confidenceList =

    skillsConfidence ?? cv.skills_confidence ?? extractionDebug?.skills_confidence ?? []

  const displaySkills =

    confidenceList.length > 0 ? confidenceList.map((s) => s.skill) : cv.skills



  return (

    <div className="section-gap animate-slide-up">

      <div className="card overflow-hidden border-emerald-200/60 p-0">

        <div className="flex items-center gap-3 border-b border-emerald-100 bg-emerald-50/60 px-6 py-4">

          <CheckCircle2 className="h-5 w-5 text-emerald-600" />

          <div>

            <h3 className="font-semibold text-slate-900">{t.upload.success}</h3>

            <p className="text-sm text-slate-600">{message ?? t.upload.extractedTitle}</p>

            {hasMatches && (topScore != null || matchesCreated != null) && (

              <p className="mt-1 text-caption text-slate-500">

                {matchesCreated ?? sorted.length} matches

                {jobsCount != null ? ` · ${jobsCount} jobs scored` : ''}

                {topScore != null ? ` · top ${Math.round(topScore)}%` : ''}

              </p>

            )}

          </div>

        </div>



        <div className="space-y-6 p-6 lg:p-8">

          <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">

            <p className="text-overline uppercase text-brand-600">{t.upload.profileLabel}</p>

            <div className="mt-3 flex items-start gap-3">

              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-brand text-sm font-bold text-white">

                {cv.full_name?.charAt(0) ?? <User className="h-5 w-5" />}

              </div>

              <div className="min-w-0 flex-1">

                <p className="font-semibold text-slate-900">{cv.full_name ?? '—'}</p>

                {cv.email && <p className="text-sm text-slate-600">{cv.email}</p>}

                <div className="mt-2 flex flex-wrap gap-2 text-caption text-slate-500">

                  {cv.years_experience != null && (

                    <span>

                      {cv.years_experience}+ {t.upload.experienceLabel}

                    </span>

                  )}

                  {extractionMethod && (

                    <span className="badge bg-white text-slate-600 ring-1 ring-slate-200">

                      {t.upload.extractionMethod}: {extractionMethod}

                    </span>

                  )}

                </div>

              </div>

            </div>

            {cv.summary && (

              <p className="mt-4 text-sm leading-relaxed text-slate-600">{cv.summary}</p>

            )}

          </div>



          {confidenceList.length > 0 ? <SkillConfidenceList skills={confidenceList} /> : null}



          {uploadResponse && (

            <ExtractionDebugPanel response={uploadResponse} skillsConfidence={confidenceList} />

          )}



          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

            <div>

              <p className="text-overline uppercase text-slate-500">{t.upload.skillsLabel}</p>

              <div className="mt-2 flex flex-wrap gap-1.5">

                {displaySkills.map((s) => (

                  <span key={s} className="badge-brand">

                    {s}

                  </span>

                ))}

              </div>

            </div>

            <div>

              <p className="text-overline uppercase text-slate-500">{t.upload.toolsLabel}</p>

              <div className="mt-2 flex flex-wrap gap-1.5">

                {cv.tools.map((s) => (

                  <span key={s} className="badge bg-slate-100 text-slate-700 ring-1 ring-slate-200">

                    {s}

                  </span>

                ))}

              </div>

            </div>

            <div>

              <p className="text-overline uppercase text-slate-500">{t.upload.titlesLabel}</p>

              <div className="mt-2 flex flex-wrap gap-1.5">

                {cv.job_titles.map((s) => (

                  <span key={s} className="badge bg-violet-50 text-violet-700 ring-1 ring-violet-100">

                    {s}

                  </span>

                ))}

              </div>

            </div>

            {cv.languages && cv.languages.length > 0 && (

              <div>

                <p className="text-overline uppercase text-slate-500">{t.upload.languagesLabel}</p>

                <div className="mt-2 flex flex-wrap gap-1.5">

                  {cv.languages.map((s) => (

                    <span key={s} className="badge bg-blue-50 text-blue-700 ring-1 ring-blue-100">

                      {s}

                    </span>

                  ))}

                </div>

              </div>

            )}

          </div>



          {rawTextPreview && (

            <div className="border-t border-slate-100 pt-4">

              <button

                type="button"

                className="flex w-full items-center justify-between gap-2 text-sm font-medium text-slate-700 hover:text-brand-600"

                onClick={() => setShowRawText((v) => !v)}

              >

                <span>{t.upload.rawTextLabel}</span>

                {showRawText ? (

                  <ChevronUp className="h-4 w-4 shrink-0" />

                ) : (

                  <ChevronDown className="h-4 w-4 shrink-0" />

                )}

              </button>

              {showRawText && (

                <pre className="mt-3 max-h-64 overflow-auto rounded-xl bg-slate-900 p-4 text-xs leading-relaxed text-slate-100 whitespace-pre-wrap">

                  {rawTextPreview}

                </pre>

              )}

              {!showRawText && (

                <p className="mt-1 text-caption text-slate-400">{t.upload.rawTextToggle}</p>

              )}

            </div>

          )}

        </div>

      </div>



      <div>

        <h3 className="mb-4 text-heading font-semibold text-slate-900">

          {t.upload.topMatches}{' '}

          {hasMatches && <span className="badge-brand align-middle">{sorted.length}</span>}

        </h3>



        {partialMatches || matchWarning ? (

          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">

            {matchWarning ?? t.upload.partialMatchesWarning}

          </div>

        ) : null}



        {!hasMatches ? (

          <div

            className="rounded-xl border border-slate-200 bg-slate-50 px-5 py-8 text-center dark:border-slate-700 dark:bg-slate-900/40"

            role="status"

          >

            <AlertCircle className="mx-auto h-8 w-8 text-slate-400" />

            <p className="mt-3 font-semibold text-slate-800 dark:text-slate-100">{t.upload.noMatchesTitle}</p>

            <p className="mx-auto mt-2 max-w-md text-sm text-slate-600 dark:text-slate-400">

              {t.upload.noMatchesHint}

            </p>

            <Link to="/dashboard" className="btn-secondary btn-sm mt-5 inline-flex">

              {t.dashboard.refreshJobs}

            </Link>

          </div>

        ) : (

          <div className="grid gap-4">

            {top.map((m) => (

              <div

                key={m.id ?? `${m.cv_profile_id}-${m.job_id}`}

                className="card relative flex flex-col gap-4 p-5 transition hover:shadow-card-hover sm:flex-row sm:items-start"

              >

                <div className="absolute end-3 top-3 z-10">

                  {m.job && <SaveJobButton jobId={m.job.id} />}

                </div>

                <MatchScoreRing score={m.match_score} size="md" />

                <div className="min-w-0 flex-1">

                  {m.job ? (

                    <>

                      <Link

                        to={`/jobs/${m.job_id}`}

                        className="text-lg font-semibold text-slate-900 transition hover:text-brand-600"

                      >

                        {m.job.title}

                      </Link>

                      <p className="text-sm text-slate-600">

                        {m.job.company} · {m.job.location}

                      </p>

                    </>

                  ) : (

                    <p className="text-sm text-slate-500">Job #{m.job_id}</p>

                  )}

                  <div className="mt-4">

                    <MatchInsightPanel match={m} compact />

                  </div>

                </div>

              </div>

            ))}

          </div>

        )}

      </div>



      <Link to="/dashboard" className="btn-primary inline-flex">

        {t.upload.viewDashboard}

        <ArrowRight className="h-4 w-4" />

      </Link>

    </div>

  )

}


