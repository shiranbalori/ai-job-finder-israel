import { Star } from 'lucide-react'
import { useApp } from '../context/AppContext'

interface Props {
  jobId: number
  /** Show text label beside icon */
  showLabel?: boolean
  className?: string
}

/**
 * Bookmark/save control — optimistic toggle, visible in light & dark mode.
 */
export default function SaveJobButton({ jobId, showLabel = false, className = '' }: Props) {
  const { savedJobIds, toggleSaveJob, t } = useApp()
  const saved = savedJobIds.has(jobId)
  const tooltip = saved ? t.dashboard.unsaveJob : t.dashboard.saveJobTooltip

  return (
    <button
      type="button"
      title={tooltip}
      aria-label={tooltip}
      className={`inline-flex items-center justify-center gap-1.5 rounded-xl border px-2.5 py-2 text-sm font-medium shadow-sm transition-all duration-150 hover:scale-105 active:scale-95 ${
        saved
          ? 'border-amber-400/80 bg-amber-50 text-amber-600 ring-1 ring-amber-200/60 dark:border-amber-500/60 dark:bg-amber-950/50 dark:text-amber-400 dark:ring-amber-800/40'
          : 'border-slate-200 bg-white text-slate-500 hover:border-amber-300 hover:bg-amber-50/50 hover:text-amber-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400 dark:hover:border-amber-600 dark:hover:bg-amber-950/30 dark:hover:text-amber-400'
      } ${className}`}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        void toggleSaveJob(jobId)
      }}
    >
      <Star
        className={`h-4 w-4 shrink-0 transition-colors ${saved ? 'fill-amber-400 text-amber-500 dark:fill-amber-400 dark:text-amber-400' : ''}`}
        strokeWidth={2}
      />
      {showLabel && (
        <span className="hidden sm:inline">{saved ? t.dashboard.savedLabel : t.dashboard.saveJob}</span>
      )}
    </button>
  )
}
