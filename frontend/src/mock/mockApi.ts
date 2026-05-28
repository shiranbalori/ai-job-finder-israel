/**
 * Mock API — simulates network delay for realistic loading states.
 */

import type {
  CVInsights,
  CVProfile,
  CVUploadResponse,
  DashboardStats,
  Job,
  JobMatch,
  SavedJobEntry,
  UserSettings,
} from '../api/client'
import {
  MOCK_COMPANIES,
  MOCK_CV,
  MOCK_JOBS,
  MOCK_MATCHES,
  MOCK_SETTINGS,
  MOCK_STATS,
} from './data'

const delay = (ms = 600) => new Promise((r) => setTimeout(r, ms))

let settings: UserSettings = { ...MOCK_SETTINGS }
let cv: CVProfile | null = null
let matches: JobMatch[] = []
let stats: DashboardStats = { ...MOCK_STATS, cv_profile_id: null, matched_jobs: 0, avg_match_score: 0 }
const savedJobIds = new Set<number>()

export const mockApi = {
  async health() {
    await delay(200)
    return { status: 'ok', app: 'AI Job Finder Israel (mock)' }
  },

  async getSettings(): Promise<UserSettings> {
    await delay(300)
    return { ...settings }
  },

  async updateSettings(data: Partial<UserSettings>): Promise<UserSettings> {
    await delay(400)
    settings = { ...settings, ...data }
    return { ...settings }
  },

  async getLatestCV(): Promise<CVProfile | null> {
    await delay(300)
    return cv ? { ...cv } : null
  },

  async uploadCV(_file: File): Promise<CVUploadResponse> {
    await delay(1500)
    cv = {
      ...MOCK_CV,
      id: 2,
      is_demo: false,
      source_filename: _file.name,
      full_name: 'Uploaded CV Profile',
    }
    matches = MOCK_MATCHES.map((m, i) => ({
      ...m,
      id: i + 20,
      cv_profile_id: 2,
      match_score: Math.max(55, m.match_score - 5),
    }))
    stats = computeStats(cv.id, matches)
    settings = { ...settings, demo_mode: false }
    return {
      cv_profile: { ...cv },
      matches: [...matches],
      total_jobs_scored: matches.length,
      message: 'CV uploaded — skills extracted and jobs matched (mock).',
    }
  },

  async getJobs(params?: Record<string, string>): Promise<Job[]> {
    await delay(400)
    let jobs = [...MOCK_JOBS]
    if (params?.category) jobs = jobs.filter((j) => j.category === params.category)
    if (params?.language) jobs = jobs.filter((j) => j.language === params.language)
    if (params?.search) {
      const q = params.search.toLowerCase()
      jobs = jobs.filter(
        (j) =>
          j.title.toLowerCase().includes(q) ||
          j.company.toLowerCase().includes(q) ||
          j.location.toLowerCase().includes(q),
      )
    }
    return jobs
  },

  async getJob(id: number): Promise<Job> {
    await delay(300)
    const job = MOCK_JOBS.find((j) => j.id === id)
    if (!job) throw new Error('Job not found')
    return { ...job }
  },

  async getCategories(): Promise<string[]> {
    return [...new Set(MOCK_JOBS.map((j) => j.category))].sort()
  },

  async getMatches(cvId?: number, minScore = 0): Promise<JobMatch[]> {
    await delay(500)
    return matches
      .filter((m) => (!cvId || m.cv_profile_id === cvId) && m.match_score >= minScore)
      .sort((a, b) => b.match_score - a.match_score)
  },

  async getMatch(id: number): Promise<JobMatch> {
    await delay(300)
    const m = matches.find((x) => x.id === id) ?? MOCK_MATCHES.find((x) => x.id === id)
    if (!m) throw new Error('Match not found')
    return { ...m }
  },

  async getDashboardStats(cvId?: number): Promise<DashboardStats> {
    await delay(400)
    if (cvId && cv) return computeStats(cvId, matches)
    return { ...stats }
  },

  async activateDemo() {
    await delay(2800)
    cv = { ...MOCK_CV }
    matches = MOCK_MATCHES.map((m) => ({
      ...m,
      job: MOCK_JOBS.find((j) => j.id === m.job_id) ?? m.job,
    }))
    stats = { ...computeStats(cv.id, matches), demo_mode: true }
    settings = { ...settings, demo_mode: true }
    return {
      cv_profile: { ...cv },
      matches: [...matches],
      stats,
      message: 'Demo mode activated — explore matched Israeli AI/Data jobs!',
    }
  },

  async sendDigest() {
    await delay(800)
    return {
      sent: false,
      message: 'Mock mode: digest preview only (no real email sent).',
      count: matches.filter((m) => m.match_score >= settings.min_match_score).length,
      preview_only: true,
      html_preview: '<html><body style="font-family:sans-serif;padding:24px"><h2>Mock digest preview</h2><p>Connect backend for real HTML template.</p></body></html>',
    }
  },

  async getEmailStatus() {
    await delay(100)
    return {
      smtp_configured: false,
      daily_email_enabled: false,
      from_address: 'noreply@aijobfinder.co.il',
    }
  },

  async getEmailLogs(limit = 10) {
    await delay(200)
    const now = new Date().toISOString()
    return [
      {
        id: 1,
        recipient: settings.email,
        subject: 'Your daily AI job matches — Israel',
        match_count: 3,
        sent: false,
        preview_only: true,
        created_at: now,
      },
    ].slice(0, limit)
  },

  async getSchedulerLogs(limit = 10) {
    await delay(200)
    const now = new Date().toISOString()
    return [
      {
        id: 1,
        job_name: 'daily_digest',
        status: 'skipped',
        message: 'Mock mode — scheduler not running',
        match_count: 0,
        sent: false,
        preview_only: true,
        duration_ms: 12,
        created_at: now,
      },
    ].slice(0, limit)
  },

  async getCVInsights(_cvId?: number): Promise<CVInsights> {
    await delay(300)
    const matched = matches.flatMap((m) => m.matched_skills)
    const missing = matches.flatMap((m) => m.missing_skills)
    const countMatched = (skill: string) => matched.filter((s) => s === skill).length
    const countMissing = (skill: string) => missing.filter((s) => s === skill).length
    const topMatched = [...new Set(matched)].slice(0, 6)
    const topMissing = [...new Set(missing)].slice(0, 6)
    return {
      cv_profile_id: cv?.id ?? null,
      strongest_skills: topMatched.map((skill) => ({
        skill,
        count: countMatched(skill),
        in_cv: cv?.skills.includes(skill) ?? true,
      })),
      missing_high_value_skills: topMissing.map((skill) => ({
        skill,
        count: countMissing(skill),
        in_cv: cv?.skills.includes(skill) ?? false,
      })),
      recommended_learning: topMissing.slice(0, 4),
      career_recommendations: [
        'Your profile aligns with applied AI roles in Israel — target ML Engineer and AI Automation positions.',
        'Best-fit categories: AI / ML, Data Engineering.',
        'Upskilling in Transformers and MLOps would unlock higher-score matches.',
      ],
    }
  },

  async getSavedJobs(): Promise<SavedJobEntry[]> {
    await delay(200)
    return [...savedJobIds].map((jobId, i) => ({
      id: i + 1,
      job_id: jobId,
      created_at: new Date().toISOString(),
      job: MOCK_JOBS.find((j) => j.id === jobId) ?? null,
    }))
  },

  async saveJob(jobId: number): Promise<SavedJobEntry> {
    await delay(150)
    savedJobIds.add(jobId)
    const job = MOCK_JOBS.find((j) => j.id === jobId) ?? null
    return { id: savedJobIds.size, job_id: jobId, created_at: new Date().toISOString(), job }
  },

  async unsaveJob(jobId: number) {
    await delay(150)
    savedJobIds.delete(jobId)
    return { message: 'Job removed from saved list.' }
  },

  getCompanies: () => MOCK_COMPANIES,
}

function computeStats(cvId: number, list: JobMatch[]): DashboardStats {
  const scores = list.map((m) => m.match_score)
  const missing = list.flatMap((m) => m.missing_skills)
  const matched = list.flatMap((m) => m.matched_skills)
  const counts = missing.reduce<Record<string, number>>((acc, s) => {
    acc[s] = (acc[s] ?? 0) + 1
    return acc
  }, {})
  const matchedCounts = matched.reduce<Record<string, number>>((acc, s) => {
    acc[s] = (acc[s] ?? 0) + 1
    return acc
  }, {})
  const top_missing = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([s]) => s)

  const companyMap = new Map<string, number[]>()
  const categoryMap = new Map<string, number[]>()
  for (const m of list) {
    if (!m.job) continue
    const co = companyMap.get(m.job.company) ?? []
    co.push(m.match_score)
    companyMap.set(m.job.company, co)
    const cat = categoryMap.get(m.job.category) ?? []
    cat.push(m.match_score)
    categoryMap.set(m.job.category, cat)
  }

  return {
    total_jobs: MOCK_JOBS.length,
    matched_jobs: list.length,
    avg_match_score: scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0,
    top_missing_skills: top_missing,
    strongest_skills: Object.entries(matchedCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([s]) => s),
    top_companies: [...companyMap.entries()]
      .map(([company, vals]) => ({
        company,
        count: vals.length,
        avg_score: Math.round(vals.reduce((a, b) => a + b, 0) / vals.length),
      }))
      .sort((a, b) => b.avg_score - a.avg_score)
      .slice(0, 5),
    role_distribution: [...categoryMap.entries()]
      .map(([category, vals]) => ({
        category,
        count: vals.length,
        avg_score: Math.round(vals.reduce((a, b) => a + b, 0) / vals.length),
      }))
      .sort((a, b) => b.count - a.count),
    cv_profile_id: cvId,
    demo_mode: settings.demo_mode,
  }
}
