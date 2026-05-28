import { Sparkles, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useApp } from '../../context/AppContext'

export default function DemoBanner() {
  const { t, demoMode, cv, matches, dismissDemoBanner, demoBannerVisible } = useApp()

  if (!demoMode || !demoBannerVisible || !cv) return null

  const topScore = matches[0]?.match_score ?? 0

  return (
    <div className="border-b border-violet-200/60 bg-gradient-to-r from-violet-50 via-brand-50 to-violet-50">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-brand text-white shadow-soft">
            <Sparkles className="h-4 w-4" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">{t.demo.bannerTitle}</p>
            <p className="text-caption text-slate-600">
              {t.demo.bannerDesc
                .replace('{name}', cv.full_name ?? '')
                .replace('{count}', String(matches.length))
                .replace('{score}', String(Math.round(topScore)))}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/dashboard" className="btn-primary btn-sm">
            {t.demo.viewMatches}
          </Link>
          <button
            type="button"
            onClick={dismissDemoBanner}
            className="btn-ghost !p-2 text-slate-400"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
