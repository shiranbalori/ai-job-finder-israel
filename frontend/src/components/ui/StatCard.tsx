import type { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: string | number
  icon: LucideIcon
  trend?: string
  accent?: 'brand' | 'emerald' | 'amber' | 'violet'
}

const accents = {
  brand: { bg: 'bg-brand-50', icon: 'from-brand-500 to-brand-600', ring: 'ring-brand-100' },
  emerald: { bg: 'bg-emerald-50', icon: 'from-emerald-500 to-teal-600', ring: 'ring-emerald-100' },
  amber: { bg: 'bg-amber-50', icon: 'from-amber-500 to-orange-500', ring: 'ring-amber-100' },
  violet: { bg: 'bg-violet-50', icon: 'from-violet-500 to-purple-600', ring: 'ring-violet-100' },
}

export default function StatCard({ label, value, icon: Icon, trend, accent = 'brand' }: Props) {
  const a = accents[accent]

  return (
    <div className="card group relative overflow-hidden p-5 transition-all hover:shadow-card-hover dark:hover:border-slate-600 lg:p-6">
      <div className={`absolute -end-4 -top-4 h-24 w-24 rounded-full ${a.bg} opacity-60 blur-2xl transition group-hover:opacity-80`} />
      <div className="relative flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-overline uppercase text-slate-500 dark:text-slate-400">{label}</p>
          <p className="mt-2 truncate text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 lg:text-3xl">
            {value}
          </p>
          {trend && (
            <p className="mt-1.5 flex items-center gap-1 text-caption font-medium text-emerald-600">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
              {trend}
            </p>
          )}
        </div>
        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${a.icon} text-white shadow-soft ring-2 ${a.ring} transition group-hover:scale-105`}
        >
          <Icon className="h-5 w-5" strokeWidth={2} />
        </div>
      </div>
    </div>
  )
}
