import { Mail, MapPin, User } from 'lucide-react'
import type { CVProfile } from '../../api/client'
import { useApp } from '../../context/AppContext'

interface Props {
  cv: CVProfile
}

/** Rich demo CV profile card — looks like a real parsed resume. */
export default function DemoProfileCard({ cv }: Props) {
  const { t } = useApp()

  return (
    <div className="card overflow-hidden border-brand-100 p-0">
      <div className="bg-gradient-to-r from-brand-600 to-violet-600 px-6 py-4 text-white">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/20 text-2xl font-bold backdrop-blur">
              {cv.full_name?.charAt(0) ?? <User className="h-7 w-7" />}
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-brand-100">
                {cv.is_demo ? t.demo.demoProfileLabel : t.dashboard.activeProfile}
              </p>
              <h2 className="text-xl font-bold">{cv.full_name}</h2>
              <p className="text-sm text-brand-100">{cv.job_titles[0]}</p>
            </div>
          </div>
          {cv.is_demo && (
            <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-bold backdrop-blur">
              {t.demo.sampleData}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-5 p-6">
        <p className="text-sm leading-relaxed text-slate-600">{cv.summary}</p>

        <div className="flex flex-wrap gap-4 text-sm text-slate-500">
          <span className="flex items-center gap-1.5">
            <MapPin className="h-4 w-4 text-brand-500" />
            Tel Aviv, Israel
          </span>
          <span className="flex items-center gap-1.5">
            <Mail className="h-4 w-4 text-brand-500" />
            {cv.email}
          </span>
          <span className="font-semibold text-brand-600">
            {cv.years_experience}+ {t.dashboard.yearsLabel}
          </span>
        </div>

        <div>
          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
            {t.upload.skillsLabel}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {cv.skills.map((s) => (
              <span key={s} className="badge bg-brand-50 text-brand-700">
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
              {t.upload.toolsLabel}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {cv.tools.map((s) => (
                <span key={s} className="badge bg-slate-100 text-slate-700">
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">
              {t.demo.techStack}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {cv.technologies.map((s) => (
                <span key={s} className="badge bg-violet-50 text-violet-700">
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
