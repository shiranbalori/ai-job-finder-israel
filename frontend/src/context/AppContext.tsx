import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  api,
  checkBackendHealth,
  USE_MOCK,
  type CVInsights,
  type CVProfile,
  type DashboardStats,
  type Job,
  type JobMatch,
  type UserSettings,
} from '../api'
import { getStoredToken } from '../api/authService'
import { type Lang, translations } from '../i18n/translations'
import { useAuth } from './AuthContext'

const DEMO_STEP_MS = 550

interface AppState {
  lang: Lang
  setLang: (l: Lang) => void
  t: (typeof translations)['en']
  dir: 'ltr' | 'rtl'
  settings: UserSettings | null
  cv: CVProfile | null
  jobs: Job[]
  matches: JobMatch[]
  stats: DashboardStats | null
  loading: boolean
  demoLoading: boolean
  demoStep: number
  demoMode: boolean
  demoBannerVisible: boolean
  backendOnline: boolean
  usingMock: boolean
  israelOnly: boolean
  setIsraelOnly: (v: boolean) => void
  cvInsights: CVInsights | null
  insightsLoading: boolean
  savedJobIds: Set<number>
  toggleSaveJob: (jobId: number) => Promise<void>
  refresh: () => Promise<void>
  activateDemo: () => Promise<void>
  dismissDemoBanner: () => void
  setCv: (cv: CVProfile | null) => void
  setMatches: (m: JobMatch[]) => void
}

const AppContext = createContext<AppState | null>(null)

/** Animate demo loading steps while API call runs in parallel. */
async function runDemoSteps(setStep: (n: number) => void, apiCall: () => Promise<void>) {
  const steps = 5
  const timers: ReturnType<typeof setTimeout>[] = []
  for (let i = 0; i < steps - 1; i++) {
    timers.push(setTimeout(() => setStep(i), i * DEMO_STEP_MS))
  }
  await Promise.all([apiCall(), new Promise((r) => setTimeout(r, (steps - 1) * DEMO_STEP_MS))])
  setStep(steps - 1)
  await new Promise((r) => setTimeout(r, 400))
  timers.forEach(clearTimeout)
}

export function AppProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  const [lang, setLangState] = useState<Lang>('en')
  const [settings, setSettings] = useState<UserSettings | null>(null)
  const [cv, setCv] = useState<CVProfile | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [matches, setMatches] = useState<JobMatch[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [demoLoading, setDemoLoading] = useState(false)
  const [demoStep, setDemoStep] = useState(0)
  const [demoBannerVisible, setDemoBannerVisible] = useState(true)
  const [backendOnline, setBackendOnline] = useState(false)
  const [usingMock, setUsingMock] = useState(USE_MOCK)
  const [israelOnly, setIsraelOnly] = useState(true)
  const [cvInsights, setCvInsights] = useState<CVInsights | null>(null)
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [savedJobIds, setSavedJobIds] = useState<Set<number>>(new Set())

  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    document.documentElement.lang = l
    document.documentElement.dir = l === 'he' ? 'rtl' : 'ltr'
  }, [])

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const health = await checkBackendHealth()
      setBackendOnline(health.ok)
      setUsingMock(health.mock)

      const hasToken = !!getStoredToken()

      if (!hasToken && !USE_MOCK) {
        setSettings(null)
        setCv(null)
        setJobs(await api.getJobs({ israel_only: String(israelOnly) }).catch(() => []))
        setMatches([])
        setStats(null)
        setCvInsights(null)
        setSavedJobIds(new Set())
        return
      }

      const [s, latestCv] = await Promise.all([
        api.getSettings().catch(() => null),
        api.getLatestCV().catch(() => null),
      ])

      setSettings(s)

      if (s?.ui_language === 'he' || s?.ui_language === 'en') {
        setLang(s.ui_language as Lang)
      }

      setCv(latestCv)

      const inDemo = s?.demo_mode || latestCv?.is_demo
      const jobParams = inDemo ? undefined : { israel_only: String(israelOnly) }
      const jobList = inDemo ? await api.getMockJobs() : await api.getJobs(jobParams)
      setJobs(jobList)

      if (latestCv) {
        setInsightsLoading(true)
        const [m, st, insights, saved] = await Promise.all([
          api.getMatches(latestCv.id, 0, inDemo ? true : israelOnly),
          api.getDashboardStats(latestCv.id, inDemo ? true : israelOnly),
          api.getCVInsights(latestCv.id, inDemo ? true : israelOnly).catch(() => null),
          api.getSavedJobs().catch(() => []),
        ])
        setMatches(m)
        setStats(st)
        setCvInsights(insights)
        setSavedJobIds(new Set(saved.map((s) => s.job_id)))
        setInsightsLoading(false)
      } else {
        setMatches([])
        setStats(await api.getDashboardStats())
        setCvInsights(null)
        setSavedJobIds(new Set())
      }
    } catch (err) {
      console.error('[App] refresh failed:', err)
      setBackendOnline(false)
    } finally {
      setLoading(false)
    }
  }, [setLang, israelOnly])

  const activateDemo = useCallback(async () => {
    setDemoLoading(true)
    setDemoStep(0)
    setDemoBannerVisible(true)

    try {
      let result: {
        cv_profile: CVProfile
        matches: JobMatch[]
        stats: DashboardStats
      } | null = null

      await runDemoSteps(setDemoStep, async () => {
        const res = await api.activateDemo()
        result = res
      })

      if (result) {
        setCv(result.cv_profile)
        setMatches(result.matches)
        setStats({ ...result.stats, demo_mode: true })
        setJobs(await api.getMockJobs())
        setSettings((prev) =>
          prev
            ? { ...prev, demo_mode: true }
            : {
                id: 1,
                email: 'demo@example.com',
                daily_digest_enabled: false,
                digest_hour: 8,
                ui_language: 'en',
                min_match_score: 50,
                demo_mode: true,
              },
        )
      }
    } finally {
      setDemoLoading(false)
      setDemoStep(0)
    }
  }, [])

  const dismissDemoBanner = useCallback(() => setDemoBannerVisible(false), [])

  const toggleSaveJob = useCallback(async (jobId: number) => {
    const wasSaved = savedJobIds.has(jobId)
    // Optimistic UI — instant feedback
    setSavedJobIds((prev) => {
      const next = new Set(prev)
      if (wasSaved) next.delete(jobId)
      else next.add(jobId)
      return next
    })
    try {
      if (wasSaved) await api.unsaveJob(jobId)
      else await api.saveJob(jobId)
    } catch (err) {
      console.error('[App] toggle save failed:', err)
      setSavedJobIds((prev) => {
        const next = new Set(prev)
        if (wasSaved) next.add(jobId)
        else next.delete(jobId)
        return next
      })
    }
  }, [savedJobIds])

  useEffect(() => {
    refresh()
  }, [refresh, isAuthenticated])

  const demoMode = settings?.demo_mode ?? stats?.demo_mode ?? cv?.is_demo ?? false

  const value = useMemo<AppState>(
    () => ({
      lang,
      setLang,
      t: translations[lang],
      dir: lang === 'he' ? 'rtl' : 'ltr',
      settings,
      cv,
      jobs,
      matches,
      stats,
      loading,
      demoLoading,
      demoStep,
      demoMode,
      demoBannerVisible,
      backendOnline,
      usingMock,
      israelOnly,
      setIsraelOnly,
      cvInsights,
      insightsLoading,
      savedJobIds,
      toggleSaveJob,
      refresh,
      activateDemo,
      dismissDemoBanner,
      setCv,
      setMatches,
    }),
    [
      lang,
      setLang,
      settings,
      cv,
      jobs,
      matches,
      stats,
      loading,
      demoLoading,
      demoStep,
      demoMode,
      demoBannerVisible,
      backendOnline,
      usingMock,
      israelOnly,
      cvInsights,
      insightsLoading,
      savedJobIds,
      toggleSaveJob,
      refresh,
      activateDemo,
      dismissDemoBanner,
    ],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
