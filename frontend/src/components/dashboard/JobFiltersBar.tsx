import { ArrowDownUp, Bookmark, Filter, MapPin, SlidersHorizontal } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export type SortOption = 'score' | 'newest' | 'semantic'
export type WorkModeFilter = '' | 'remote' | 'hybrid' | 'onsite'

export interface JobFilterState {
  search: string
  minScore: number
  category: string
  company: string
  city: string
  workMode: WorkModeFilter
  sortBy: SortOption
  savedOnly: boolean
}

interface Props {
  filters: JobFilterState
  onChange: (patch: Partial<JobFilterState>) => void
  categories: string[]
  companies: string[]
  cities: string[]
  resultCount: number
}

export default function JobFiltersBar({
  filters,
  onChange,
  categories,
  companies,
  cities,
  resultCount,
}: Props) {
  const { t, demoMode, israelOnly, setIsraelOnly } = useApp()

  return (
    <div className="card space-y-5 p-5">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
          <Filter className="h-4 w-4 text-brand-500" />
          {t.dashboard.filters}
        </h2>
        <span className="badge-brand">{resultCount}</span>
      </div>

      <div>
        <label className="label">{t.dashboard.search}</label>
        <input
          className="input"
          placeholder={t.dashboard.search}
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value })}
        />
      </div>

      <div>
        <label className="label flex justify-between">
          <span>{t.dashboard.minScore}</span>
          <span className="font-semibold text-brand-600 dark:text-brand-400">
            {filters.minScore}%+
          </span>
        </label>
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={filters.minScore}
          onChange={(e) => onChange({ minScore: Number(e.target.value) })}
          className="w-full accent-brand-600"
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="label">{t.dashboard.category}</label>
          <select
            className="input"
            value={filters.category}
            onChange={(e) => onChange({ category: e.target.value })}
          >
            <option value="">{t.dashboard.all}</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">{t.dashboard.company}</label>
          <select
            className="input"
            value={filters.company}
            onChange={(e) => onChange({ company: e.target.value })}
          >
            <option value="">{t.dashboard.allCompanies}</option>
            {companies.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="label flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5" />
            {t.dashboard.city}
          </label>
          <select
            className="input"
            value={filters.city}
            onChange={(e) => onChange({ city: e.target.value })}
          >
            <option value="">{t.dashboard.allCities}</option>
            {cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label flex items-center gap-1">
            <SlidersHorizontal className="h-3.5 w-3.5" />
            {t.dashboard.workMode}
          </label>
          <select
            className="input"
            value={filters.workMode}
            onChange={(e) => onChange({ workMode: e.target.value as WorkModeFilter })}
          >
            <option value="">{t.dashboard.allWorkModes}</option>
            <option value="remote">{t.dashboard.remote}</option>
            <option value="hybrid">{t.dashboard.hybrid}</option>
            <option value="onsite">{t.dashboard.onsite}</option>
          </select>
        </div>
      </div>

      <div>
        <label className="label flex items-center gap-1">
          <ArrowDownUp className="h-3.5 w-3.5" />
          {t.dashboard.sortBy}
        </label>
        <select
          className="input"
          value={filters.sortBy}
          onChange={(e) => onChange({ sortBy: e.target.value as SortOption })}
        >
          <option value="score">{t.dashboard.sortScore}</option>
          <option value="newest">{t.dashboard.sortNewest}</option>
          <option value="semantic">{t.dashboard.sortSemantic}</option>
        </select>
      </div>

      <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 dark:border-slate-600 dark:bg-slate-800/50">
        <input
          type="checkbox"
          className="rounded accent-brand-600"
          checked={filters.savedOnly}
          onChange={(e) => onChange({ savedOnly: e.target.checked })}
        />
        <span className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
          <Bookmark className="h-4 w-4 text-brand-500" />
          {t.dashboard.savedOnly}
        </span>
      </label>

      {!demoMode && (
        <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 dark:border-slate-600 dark:bg-slate-800/50">
          <input
            type="checkbox"
            className="mt-0.5 rounded accent-brand-600"
            checked={israelOnly}
            onChange={(e) => setIsraelOnly(e.target.checked)}
          />
          <span>
            <span className="block text-sm font-medium text-slate-900 dark:text-slate-100">
              {t.dashboard.israelOnly}
            </span>
            <span className="mt-0.5 block text-caption text-slate-500">{t.dashboard.israelOnlyHint}</span>
          </span>
        </label>
      )}
    </div>
  )
}
