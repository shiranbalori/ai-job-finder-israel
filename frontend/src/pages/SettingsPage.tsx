import { useEffect, useState } from 'react'

import { Bell, Bookmark, Clock, Globe, History, Mail, Save, Send, Tag } from 'lucide-react'

import { api } from '../api'

import type { EmailDigestResponse, EmailLogEntry, EmailStatus, SchedulerLogEntry } from '../api/client'

import { useApp } from '../context/AppContext'

import PageHeader from '../components/ui/PageHeader'



export default function SettingsPage() {

  const { t, settings, refresh, lang, setLang, demoMode } = useApp()

  const [email, setEmail] = useState('')

  const [digest, setDigest] = useState(false)

  const [hour, setHour] = useState(8)

  const [minScore, setMinScore] = useState(50)

  const [keywords, setKeywords] = useState('')

  const [includeSaved, setIncludeSaved] = useState(false)

  const [saving, setSaving] = useState(false)

  const [sendingTest, setSendingTest] = useState(false)

  const [message, setMessage] = useState<string | null>(null)

  const [messageKind, setMessageKind] = useState<'success' | 'error' | 'preview' | 'info'>('info')

  const [digestResult, setDigestResult] = useState<EmailDigestResponse | null>(null)

  const [showPreview, setShowPreview] = useState(false)

  const [emailStatus, setEmailStatus] = useState<EmailStatus | null>(null)

  const [emailLogs, setEmailLogs] = useState<EmailLogEntry[]>([])

  const [schedulerLogs, setSchedulerLogs] = useState<SchedulerLogEntry[]>([])



  const loadLogs = async () => {

    try {

      const [emails, scheduler, status] = await Promise.all([

        api.getEmailLogs(8),

        api.getSchedulerLogs(8),

        api.getEmailStatus(),

      ])

      setEmailLogs(emails)

      setSchedulerLogs(scheduler)

      setEmailStatus(status)

    } catch {

      /* logs are optional UI */

    }

  }



  useEffect(() => {

    if (settings) {

      setEmail(settings.email)

      setDigest(settings.daily_digest_enabled)

      setHour(settings.digest_hour)

      setMinScore(settings.min_match_score)

      setKeywords((settings.preferred_job_keywords ?? []).join(', '))

      setIncludeSaved(settings.include_saved_jobs ?? false)

    }

  }, [settings])

  useEffect(() => {
    void loadLogs()
  }, [])



  const save = async () => {

    setSaving(true)

    setMessage(null)

    setMessageKind('info')

    try {

      const keywordList = keywords

        .split(',')

        .map((k) => k.trim())

        .filter(Boolean)

      await api.updateSettings({

        email,

        daily_digest_enabled: digest,

        digest_hour: hour,

        min_match_score: minScore,

        preferred_job_keywords: keywordList,

        include_saved_jobs: includeSaved,

        ui_language: lang,

      })

      setLang(lang)

      await refresh()

      setMessage(t.settings.saved)

      setMessageKind('success')

    } catch (e) {

      setMessage(e instanceof Error ? e.message : 'Save failed')

      setMessageKind('error')

    } finally {

      setSaving(false)

    }

  }



  const testDigest = async () => {

    setMessage(null)

    setDigestResult(null)

    setSendingTest(true)

    try {

      const res = (await api.sendDigest()) as EmailDigestResponse

      setDigestResult(res)

      setMessage(res.message)

      if (res.sent) {

        setMessageKind('success')

      } else if (res.preview_only) {

        setMessageKind('preview')

      } else {

        setMessageKind('error')

      }

      if (res.html_preview) setShowPreview(true)

      await refresh()

      await loadLogs()

    } catch (e) {

      setMessage(e instanceof Error ? e.message : 'Failed to send test email')

      setMessageKind('error')

    } finally {

      setSendingTest(false)

    }

  }



  const messageStyles = {

    success: 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200',

    error: 'border-rose-200 bg-rose-50 text-rose-900 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200',

    preview: 'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200',

    info: 'border-brand-100 bg-brand-50 text-brand-800 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-200',

  }[messageKind]



  return (

    <div className="page-container">

      <PageHeader title={t.settings.title} subtitle={t.settings.subtitle} />



      <div className="mx-auto grid max-w-2xl gap-6">

        {demoMode && (

          <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">

            {t.settings.demoEmailNote}

          </p>

        )}



        {emailStatus && (

          <p

            className={`rounded-xl border px-4 py-3 text-sm ${

              emailStatus.smtp_configured

                ? 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200'

                : 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-600 dark:bg-slate-800/50 dark:text-slate-300'

            }`}

          >

            {emailStatus.smtp_configured ? t.settings.smtpConfigured : t.settings.smtpNotConfigured}

            {emailStatus.smtp_configured && (

              <span className="mt-1 block text-xs opacity-80">

                From: {emailStatus.from_address}

              </span>

            )}

          </p>

        )}



        <div className="card space-y-6 p-6 lg:p-8">

          <div className="flex items-center gap-4 border-b border-slate-100 pb-5">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100">

              <Mail className="h-5 w-5" />

            </div>

            <div>

              <h2 className="font-semibold text-slate-900">{t.settings.emailSection}</h2>

              <p className="text-sm text-slate-500">{t.settings.emailSectionDesc}</p>

            </div>

          </div>



          <div>

            <label className="label">{t.settings.email}</label>

            <input

              className="input"

              type="email"

              value={email}

              onChange={(e) => setEmail(e.target.value)}

              placeholder="you@example.com"

            />

          </div>



          <label className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 transition hover:border-brand-200 hover:bg-brand-50/30">

            <div className="flex items-center gap-3">

              <Bell className="h-5 w-5 text-brand-500" />

              <span className="text-sm font-medium text-slate-700">{t.settings.digest}</span>

            </div>

            <input

              type="checkbox"

              checked={digest}

              onChange={(e) => setDigest(e.target.checked)}

              className="h-5 w-5 rounded accent-brand-600"

            />

          </label>



          <label className="flex cursor-pointer items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/50 p-4 transition hover:border-brand-200 hover:bg-brand-50/30 dark:border-slate-600 dark:bg-slate-800/50 dark:hover:border-brand-700">

            <div className="flex items-center gap-3">

              <Bookmark className="h-5 w-5 text-amber-500" />

              <div>

                <span className="block text-sm font-medium text-slate-700 dark:text-slate-200">

                  {t.settings.includeSavedJobs}

                </span>

                <span className="mt-0.5 block text-caption text-slate-500 dark:text-slate-400">

                  {t.settings.includeSavedJobsHint}

                </span>

              </div>

            </div>

            <input

              type="checkbox"

              checked={includeSaved}

              onChange={(e) => setIncludeSaved(e.target.checked)}

              className="h-5 w-5 rounded accent-brand-600"

            />

          </label>



          <div>

            <label className="label flex items-center gap-2">

              <Clock className="h-4 w-4 text-slate-400" />

              {t.settings.hour}

            </label>

            <input

              className="input"

              type="number"

              min={0}

              max={23}

              value={hour}

              onChange={(e) => setHour(Number(e.target.value))}

            />

          </div>



          <div>

            <label className="label">

              {t.settings.minScore}: <span className="font-bold text-brand-600">{minScore}%</span>

            </label>

            <input

              type="range"

              min={0}

              max={100}

              step={5}

              value={minScore}

              onChange={(e) => setMinScore(Number(e.target.value))}

              className="mt-2 w-full accent-brand-600"

            />

            <div className="mt-1 flex justify-between text-caption text-slate-400">

              <span>0%</span>

              <span>100%</span>

            </div>

          </div>



          <div>

            <label className="label flex items-center gap-2">

              <Tag className="h-4 w-4 text-slate-400" />

              {t.settings.keywords}

            </label>

            <input

              className="input"

              type="text"

              value={keywords}

              onChange={(e) => setKeywords(e.target.value)}

              placeholder={t.settings.keywordsPlaceholder}

            />

            <p className="mt-1 text-caption text-slate-400">{t.settings.keywordsHint}</p>

          </div>



          {settings?.last_digest_sent_at && (

            <p className="text-sm text-slate-500">

              {t.settings.lastSent}:{' '}

              <span className="font-medium text-slate-700">

                {new Date(settings.last_digest_sent_at).toLocaleString()}

              </span>

            </p>

          )}

        </div>



        <div className="card space-y-4 p-6 lg:p-8">

          <div className="flex items-center gap-3">

            <Globe className="h-5 w-5 text-brand-500" />

            <h2 className="font-semibold text-slate-900">{t.settings.language}</h2>

          </div>

          <div className="grid grid-cols-2 gap-3">

            {(['en', 'he'] as const).map((l) => (

              <button

                key={l}

                type="button"

                onClick={() => setLang(l)}

                className={`rounded-xl border py-3.5 text-sm font-semibold transition ${

                  lang === l

                    ? 'border-brand-500 bg-brand-50 text-brand-700 shadow-sm ring-1 ring-brand-100'

                    : 'border-slate-200 text-slate-600 hover:border-brand-200 hover:bg-slate-50'

                }`}

              >

                {l === 'en' ? 'English' : 'עברית'}

              </button>

            ))}

          </div>

        </div>



        <div className="flex flex-col gap-3 sm:flex-row">

          <button type="button" className="btn-primary flex-1 sm:flex-none" onClick={save} disabled={saving}>

            <Save className="h-4 w-4" />

            {saving ? t.loading : t.settings.save}

          </button>

          <button type="button" className="btn-secondary flex-1 sm:flex-none" onClick={testDigest} disabled={sendingTest}>

            <Send className="h-4 w-4" />

            {sendingTest ? t.loading : t.settings.testEmail}

          </button>

        </div>



        {message && (

          <p className={`rounded-xl border px-4 py-3 text-sm ${messageStyles}`}>

            {message}

            {digestResult && (

              <span className="mt-1 block opacity-90">

                {digestResult.count} {t.settings.jobsIncluded}

                {digestResult.preview_only ? ` · ${t.settings.previewOnly}` : ''}

              </span>

            )}

          </p>

        )}



        {showPreview && digestResult?.html_preview && (

          <div className="card overflow-hidden p-0">

            <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">

              <p className="text-sm font-semibold text-slate-800">{t.settings.emailPreview}</p>

              <button

                type="button"

                className="text-sm text-brand-600 hover:underline"

                onClick={() => setShowPreview(false)}

              >

                {t.settings.hidePreview}

              </button>

            </div>

            <iframe

              title="Email preview"

              srcDoc={digestResult.html_preview}

              className="h-[480px] w-full border-0 bg-white"

              sandbox=""

            />

          </div>

        )}



        <p className="text-caption text-slate-400">{t.settings.smtpNote}</p>



        <div className="card space-y-4 p-6 lg:p-8">

          <div className="flex items-center gap-3">

            <History className="h-5 w-5 text-brand-500" />

            <h2 className="font-semibold text-slate-900">{t.settings.emailLogs}</h2>

          </div>

          {emailLogs.length === 0 ? (

            <p className="text-sm text-slate-500">{t.settings.noLogs}</p>

          ) : (

            <div className="overflow-x-auto">

              <table className="w-full text-left text-sm">

                <thead>

                  <tr className="border-b border-slate-100 text-caption text-slate-500">

                    <th className="py-2 pr-3">{t.settings.logWhen}</th>

                    <th className="py-2 pr-3">{t.settings.logMatches}</th>

                    <th className="py-2 pr-3">{t.settings.logStatus}</th>

                  </tr>

                </thead>

                <tbody>

                  {emailLogs.map((log) => (

                    <tr key={log.id} className="border-b border-slate-50">

                      <td className="py-2 pr-3 text-slate-600">

                        {new Date(log.created_at).toLocaleString()}

                      </td>

                      <td className="py-2 pr-3 text-slate-700">{log.match_count}</td>

                      <td className="py-2 pr-3">

                        {log.error_message ? (

                          <span className="text-rose-600">{t.settings.logFailed}</span>

                        ) : log.sent ? (

                          <span className="text-emerald-600">{t.settings.logSent}</span>

                        ) : (

                          <span className="text-amber-600">{t.settings.logPreview}</span>

                        )}

                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          )}

        </div>



        <div className="card space-y-4 p-6 lg:p-8">

          <div className="flex items-center gap-3">

            <Clock className="h-5 w-5 text-brand-500" />

            <h2 className="font-semibold text-slate-900">{t.settings.schedulerLogs}</h2>

          </div>

          {schedulerLogs.length === 0 ? (

            <p className="text-sm text-slate-500">{t.settings.noLogs}</p>

          ) : (

            <div className="overflow-x-auto">

              <table className="w-full text-left text-sm">

                <thead>

                  <tr className="border-b border-slate-100 text-caption text-slate-500">

                    <th className="py-2 pr-3">{t.settings.logWhen}</th>

                    <th className="py-2 pr-3">{t.settings.logStatus}</th>

                    <th className="py-2 pr-3">{t.settings.logMatches}</th>

                    <th className="py-2 pr-3">{t.settings.logDuration}</th>

                  </tr>

                </thead>

                <tbody>

                  {schedulerLogs.map((log) => (

                    <tr key={log.id} className="border-b border-slate-50">

                      <td className="py-2 pr-3 text-slate-600">

                        {new Date(log.created_at).toLocaleString()}

                      </td>

                      <td className="py-2 pr-3 capitalize text-slate-700">{log.status}</td>

                      <td className="py-2 pr-3 text-slate-700">{log.match_count}</td>

                      <td className="py-2 pr-3 text-slate-500">

                        {log.duration_ms != null ? `${log.duration_ms}ms` : '—'}

                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          )}

        </div>

      </div>

    </div>

  )

}


