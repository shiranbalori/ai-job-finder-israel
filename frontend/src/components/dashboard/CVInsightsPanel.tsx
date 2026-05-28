import { BookOpen, Brain, Lightbulb, Target } from 'lucide-react'
import type { CVInsights } from '../api/client'
import { useApp } from '../../context/AppContext'

interface Props {
  insights: CVInsights | null
  loading?: boolean
}

export default function CVInsightsPanel({ insights, loading }: Props) {
  const { t } = useApp()

  if (loading) {
    return (
      <div className="card space-y-4 p-6">
        <div className="skeleton-shimmer h-5 w-40" />
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton-shimmer h-24 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (!insights) return null

  return (
    <section className="card overflow-hidden p-0">
      <div className="border-b border-slate-100 bg-gradient-to-r from-brand-50/80 to-violet-50/50 px-6 py-5 dark:border-slate-700 dark:from-brand-950/40 dark:to-violet-950/30 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-brand text-white shadow-soft">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <p className="text-overline uppercase text-brand-600 dark:text-brand-400">
              {t.dashboard.aiInsights}
            </p>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              {t.dashboard.cvInsightsTitle}
            </h2>
          </div>
        </div>
      </div>

      <div className="grid gap-0 divide-y divide-slate-100 dark:divide-slate-700 sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-4 lg:divide-x">
        <InsightBlock
          icon={Target}
          title={t.dashboard.strongestSkills}
          items={insights.strongest_skills.slice(0, 5).map((s) => s.skill)}
          variant="success"
        />
        <InsightBlock
          icon={BookOpen}
          title={t.dashboard.missingSkills}
          items={insights.missing_high_value_skills.slice(0, 5).map((s) => s.skill)}
          variant="warning"
        />
        <InsightBlock
          icon={Lightbulb}
          title={t.dashboard.learningAreas}
          items={insights.recommended_learning}
          variant="brand"
        />
        <div className="p-5 lg:p-6">
          <div className="mb-3 flex items-center gap-2">
            <Brain className="h-4 w-4 text-violet-500" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {t.dashboard.careerTips}
            </h3>
          </div>
          <ul className="space-y-2.5">
            {insights.career_recommendations.map((tip) => (
              <li
                key={tip}
                className="text-sm leading-relaxed text-slate-600 dark:text-slate-300 before:me-2 before:text-brand-500 before:content-['→']"
              >
                {tip}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}

function InsightBlock({
  icon: Icon,
  title,
  items,
  variant,
}: {
  icon: typeof Target
  title: string
  items: string[]
  variant: 'success' | 'warning' | 'brand'
}) {
  const badge =
    variant === 'success'
      ? 'badge-success'
      : variant === 'warning'
        ? 'badge-warning'
        : 'badge-brand'

  return (
    <div className="p-5 lg:p-6">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {items.length === 0 ? (
          <span className="text-sm text-slate-500">—</span>
        ) : (
          items.map((item) => (
            <span key={item} className={`${badge} text-[11px]`}>
              {item}
            </span>
          ))
        )}
      </div>
    </div>
  )
}
