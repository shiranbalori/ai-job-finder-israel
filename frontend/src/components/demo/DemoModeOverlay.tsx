import { Brain, Briefcase, CheckCircle2, Loader2, Sparkles, Target } from 'lucide-react'
import { useApp } from '../../context/AppContext'

const STEP_ICONS = [Brain, Target, Briefcase, Sparkles, CheckCircle2]

export default function DemoModeOverlay() {
  const { t, demoLoading, demoStep } = useApp()

  if (!demoLoading) return null

  const steps = t.demo.steps

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md animate-slide-up rounded-3xl bg-white p-8 shadow-glow">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-soft">
            <Sparkles className="h-8 w-8 animate-pulse-soft" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">{t.demo.overlayTitle}</h2>
          <p className="mt-2 text-sm text-slate-500">{t.demo.overlaySubtitle}</p>
        </div>

        <ul className="space-y-4">
          {steps.map((label, i) => {
            const Icon = STEP_ICONS[i] ?? Loader2
            const done = demoStep > i
            const active = demoStep === i
            return (
              <li
                key={label}
                className={`flex items-center gap-3 rounded-xl px-4 py-3 transition ${
                  active
                    ? 'bg-brand-50 ring-2 ring-brand-200'
                    : done
                      ? 'bg-emerald-50/50'
                      : 'bg-slate-50 opacity-60'
                }`}
              >
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                    done
                      ? 'bg-emerald-500 text-white'
                      : active
                        ? 'bg-gradient-brand text-white'
                        : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {done ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : active ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                <span
                  className={`text-sm font-medium ${
                    active ? 'text-brand-800' : done ? 'text-emerald-800' : 'text-slate-500'
                  }`}
                >
                  {label}
                </span>
              </li>
            )
          })}
        </ul>

        <p className="mt-6 text-center text-xs text-slate-400">{t.demo.noApiKeys}</p>
      </div>
    </div>
  )
}
