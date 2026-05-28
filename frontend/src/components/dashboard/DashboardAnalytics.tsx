import { Building2, Layers, Sparkles, TrendingUp } from 'lucide-react'
import type { DashboardStats } from '../api/client'
import { useApp } from '../../context/AppContext'

interface Props {
  stats: DashboardStats
}

export default function DashboardAnalytics({ stats }: Props) {
  const { t } = useApp()

  const maxRole = Math.max(...stats.role_distribution.map((r) => r.count), 1)
  const maxCompany = Math.max(...stats.top_companies.map((c) => c.count), 1)

  return (
    <div className="stagger grid gap-4 lg:grid-cols-3">
      <div className="card p-5 lg:col-span-1">
        <div className="mb-4 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand-500" />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {t.dashboard.strongestSkills}
          </h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {(stats.strongest_skills ?? []).length === 0 ? (
            <p className="text-sm text-slate-500">{t.dashboard.noAnalytics}</p>
          ) : (
            stats.strongest_skills!.map((skill, i) => (
              <span
                key={skill}
                className="badge-success animate-fade-in text-xs"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                {skill}
              </span>
            ))
          )}
        </div>
      </div>

      <div className="card p-5 lg:col-span-1">
        <div className="mb-4 flex items-center gap-2">
          <Building2 className="h-4 w-4 text-violet-500" />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {t.dashboard.topCompanies}
          </h3>
        </div>
        <ul className="space-y-3">
          {(stats.top_companies ?? []).slice(0, 5).map((c) => (
            <li key={c.company}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="truncate font-medium text-slate-700 dark:text-slate-200">
                  {c.company}
                </span>
                <span className="shrink-0 text-caption font-semibold text-brand-600 dark:text-brand-400">
                  {c.avg_score}%
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-brand-500 transition-all duration-500"
                  style={{ width: `${(c.count / maxCompany) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="card p-5 lg:col-span-1">
        <div className="mb-4 flex items-center gap-2">
          <Layers className="h-4 w-4 text-emerald-500" />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {t.dashboard.roleDistribution}
          </h3>
        </div>
        <ul className="space-y-3">
          {(stats.role_distribution ?? []).slice(0, 5).map((r) => (
            <li key={r.category}>
              <div className="mb-1 flex items-center justify-between gap-2 text-sm">
                <span className="truncate text-slate-700 dark:text-slate-200">{r.category}</span>
                <span className="flex shrink-0 items-center gap-1 text-caption text-slate-500">
                  <TrendingUp className="h-3 w-3" />
                  {r.count}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 transition-all duration-500"
                  style={{ width: `${(r.count / maxRole) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
