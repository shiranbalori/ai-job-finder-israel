import { useCallback, useEffect, useRef, useState } from 'react'
import { AlertCircle, CheckCircle, Cloud, FileText, FileUp, Loader2, Shield } from 'lucide-react'
import type { CVProfile, CVUploadResponse, JobMatch, SkillConfidence } from '../api'
import { CVUploadError, UPLOAD_SLOW_MS, uploadRealCV, validateCVFile } from '../api/cvService'
import { useApp } from '../context/AppContext'
import PageHeader from '../components/ui/PageHeader'
import UploadResults from '../components/UploadResults'
import BackendStatus from '../components/BackendStatus'

const PROGRESS_STEPS = [
  'uploading',
  'extracting_text',
  'extracting_skills',
  'matching',
  'preparing',
] as const

type UploadResult = {
  cv: CVProfile
  matches: JobMatch[]
  rawTextPreview?: string | null
  extractionMethod?: string
  skillsConfidence?: SkillConfidence[]
  extractionDebug?: CVUploadResponse['extraction_debug']
  uploadResponse?: CVUploadResponse
  message?: string
  matchWarning?: string | null
  partialMatches?: boolean
  matchesCreated?: number
  jobsCount?: number
  topScore?: number | null
}

function stepIndexForElapsed(ms: number): number {
  if (ms < 1200) return 0
  if (ms < 3500) return 1
  if (ms < 7000) return 2
  return 3
}

export default function UploadPage() {
  const { t, refresh, setCv, setMatches, demoMode, backendOnline, usingMock } = useApp()
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [step, setStep] = useState(0)
  const [slowWarning, setSlowWarning] = useState(false)
  const [error, setError] = useState<{ message: string; code?: string } | null>(null)
  const [result, setResult] = useState<UploadResult | null>(null)
  const uploadStartedRef = useRef<number | null>(null)
  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const clearProgressTimer = () => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }
  }

  useEffect(() => () => clearProgressTimer(), [])

  const handleFile = useCallback(
    async (file: File) => {
      const validationError = validateCVFile(file)
      if (validationError) {
        setError({ message: validationError, code: 'validation' })
        return
      }

      setError(null)
      setResult(null)
      setUploading(true)
      setSlowWarning(false)
      setStep(0)
      uploadStartedRef.current = Date.now()

      clearProgressTimer()
      progressTimerRef.current = setInterval(() => {
        const started = uploadStartedRef.current
        if (!started) return
        const elapsed = Date.now() - started
        setStep(stepIndexForElapsed(elapsed))
        if (elapsed >= UPLOAD_SLOW_MS) setSlowWarning(true)
      }, 400)

      try {
        const response: CVUploadResponse = await uploadRealCV(file)

        setStep(4)
        setCv(response.cv_profile)
        setMatches(response.matches)
        setResult({
          cv: response.cv_profile,
          matches: response.matches,
          rawTextPreview: response.raw_text_preview,
          extractionMethod: response.extraction_method,
          skillsConfidence: response.skills_confidence ?? response.cv_profile.skills_confidence,
          extractionDebug: response.extraction_debug,
          uploadResponse: response,
          message: response.message,
          matchWarning: response.match_warning,
          partialMatches: response.partial_matches,
          matchesCreated: response.matches_created,
          jobsCount: response.jobs_count,
          topScore: response.top_score,
        })
        void refresh()
      } catch (e) {
        const uploadErr =
          e instanceof CVUploadError
            ? e
            : new CVUploadError(e instanceof Error ? e.message : 'Upload failed')
        setError({ message: uploadErr.message, code: uploadErr.code })
        setStep(0)
      } finally {
        clearProgressTimer()
        uploadStartedRef.current = null
        setUploading(false)
      }
    },
    [refresh, setCv, setMatches],
  )

  const resetUpload = () => {
    setError(null)
    setResult(null)
    setStep(0)
    setSlowWarning(false)
  }

  const stepLabels = t.upload.progressSteps

  return (
    <div className="page-container">
      <PageHeader title={t.upload.title} subtitle={t.upload.subtitle}>
        <BackendStatus />
      </PageHeader>

      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <span className="badge-brand inline-flex items-center gap-1.5">
              <Cloud className="h-3.5 w-3.5" />
              {t.upload.realModeBadge}
            </span>
            {!usingMock && backendOnline && (
              <span className="badge-success text-[11px]">FastAPI connected</span>
            )}
          </div>
          <p className="text-caption text-slate-500 dark:text-slate-400">{t.upload.realModeHint}</p>
        </div>

        {demoMode && (
          <p className="mb-6 rounded-xl border border-violet-200/80 bg-violet-50/50 px-4 py-3 text-sm text-violet-800 dark:border-violet-800 dark:bg-violet-950/30 dark:text-violet-200">
            {t.upload.demoModeActiveHint}
          </p>
        )}

        <div className="mb-10 grid grid-cols-5 gap-1 sm:gap-3">
          {PROGRESS_STEPS.map((key, i) => {
            const done = result ? i <= 4 : uploading && step > i
            const active = uploading && step === i
            return (
              <div key={key} className="flex flex-col items-center text-center">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-2xl text-xs font-bold transition-all sm:h-11 sm:w-11 sm:text-sm ${
                    done || active
                      ? 'bg-gradient-brand text-white shadow-soft'
                      : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500'
                  } ${active ? 'ring-4 ring-brand-100 dark:ring-brand-900' : ''}`}
                >
                  {done && !active ? <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5" /> : i + 1}
                </div>
                <p className="mt-2 hidden text-[10px] font-medium leading-tight text-slate-600 dark:text-slate-400 sm:block sm:text-caption">
                  {stepLabels[key]}
                </p>
              </div>
            )
          })}
        </div>

        {!result && (
          <div
            className={`card relative overflow-hidden border-2 border-dashed p-0 transition-all duration-300 ${
              dragging ? 'scale-[1.01] border-brand-500 bg-brand-50/50 dark:bg-brand-950/20' : 'border-slate-200 dark:border-slate-700'
            } ${uploading ? 'pointer-events-none opacity-90' : 'hover:border-brand-300 hover:shadow-card-hover dark:hover:border-brand-700'}`}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragging(false)
              const file = e.dataTransfer.files[0]
              if (file) handleFile(file)
            }}
          >
            <div className="pointer-events-none absolute inset-0 bg-mesh opacity-40 dark:bg-mesh-dark" />
            <div className="relative flex flex-col items-center px-6 py-16 text-center sm:py-20">
              {uploading ? (
                <>
                  <div className="relative">
                    <div className="absolute inset-0 animate-pulse-soft rounded-full bg-brand-400/20 blur-xl" />
                    <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-card ring-1 ring-slate-200/80 dark:bg-slate-800 dark:ring-slate-600">
                      <Loader2 className="h-8 w-8 animate-spin text-brand-600 dark:text-brand-400" />
                    </div>
                  </div>
                  <p className="mt-6 text-lg font-semibold text-slate-800 dark:text-slate-100">
                    {stepLabels[PROGRESS_STEPS[step]]}
                  </p>
                  {slowWarning && (
                    <p className="mt-3 max-w-md rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
                      {t.upload.slowProcessing}
                    </p>
                  )}
                  <p className="mt-3 text-caption text-slate-400">{t.upload.backendNote}</p>
                </>
              ) : (
                <>
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-glow">
                    <FileUp className="h-8 w-8" />
                  </div>
                  <p className="mt-6 text-xl font-bold text-slate-900 dark:text-slate-100">{t.upload.drop}</p>
                  <p className="mt-2 text-slate-500 dark:text-slate-400">{t.upload.or}</p>
                  <label className="btn-primary mt-8 cursor-pointer">
                    {t.upload.browseFiles}
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.docx"
                      onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (f) handleFile(f)
                      }}
                    />
                  </label>
                  <div className="mt-8 flex flex-wrap justify-center gap-4 text-caption text-slate-500">
                    <span className="flex items-center gap-1.5">
                      <FileText className="h-4 w-4" /> PDF
                    </span>
                    <span className="flex items-center gap-1.5">
                      <FileText className="h-4 w-4" /> DOCX
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Shield className="h-4 w-4" /> {t.upload.privacy}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {error && (
          <div
            className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-4 dark:border-red-900 dark:bg-red-950/30"
            role="alert"
          >
            <div className="flex gap-3">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" />
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-red-800 dark:text-red-200">{t.upload.errorTitle}</p>
                <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error.message}</p>
                {error.code === 'offline' && (
                  <p className="mt-2 text-caption text-red-600 dark:text-red-400">{t.upload.errorOffline}</p>
                )}
                {error.code === 'timeout' && (
                  <p className="mt-2 text-caption text-red-600 dark:text-red-400">{t.upload.timeoutHint}</p>
                )}
                <button type="button" className="btn-secondary btn-sm mt-3" onClick={resetUpload}>
                  {t.upload.tryAgain}
                </button>
              </div>
            </div>
          </div>
        )}

        {result && (
          <UploadResults
            cv={result.cv}
            matches={result.matches}
            rawTextPreview={result.rawTextPreview}
            extractionMethod={result.extractionMethod}
            skillsConfidence={result.skillsConfidence}
            extractionDebug={result.extractionDebug}
            uploadResponse={result.uploadResponse}
            message={result.message}
            matchWarning={result.matchWarning}
            partialMatches={result.partialMatches}
            matchesCreated={result.matchesCreated}
            jobsCount={result.jobsCount}
            topScore={result.topScore}
          />
        )}
      </div>
    </div>
  )
}
