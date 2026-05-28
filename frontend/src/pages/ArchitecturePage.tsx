import {
  Brain,
  Database,
  Layers,
  Mail,
  Server,
  Sparkles,
  Upload,
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import PageHeader from '../components/ui/PageHeader'
import DemoModeButton from '../components/DemoModeButton'

const stack = [
  { name: 'React + Vite', role: 'Frontend SPA' },
  { name: 'Tailwind CSS', role: 'Design system' },
  { name: 'FastAPI', role: 'REST API' },
  { name: 'SQLite', role: 'Persistence' },
  { name: 'OpenAI / Gemini', role: 'AI (optional)' },
  { name: 'SMTP + Cron', role: 'Daily digest' },
]

const flowSteps = [
  { icon: Upload, label: 'Upload CV' },
  { icon: Brain, label: 'AI Parse' },
  { icon: Sparkles, label: 'Match Jobs' },
  { icon: Database, label: 'Save Results' },
  { icon: Mail, label: 'Daily Email' },
] as const

export default function ArchitecturePage() {
  const { t } = useApp()

  return (
    <div className="page-container">
      <PageHeader
        title={t.architecture.title}
        subtitle={t.architecture.subtitle}
        badge="Portfolio"
      >
        <DemoModeButton />
      </PageHeader>

      <div className="card mb-8 overflow-x-auto p-6 lg:p-8">
        <h2 className="mb-8 text-heading font-semibold text-slate-900">{t.architecture.flowTitle}</h2>
        <div className="flex min-w-[640px] items-center justify-between gap-2">
          {flowSteps.map((step, i, arr) => (
            <div key={step.label} className="flex flex-1 items-center">
              <div className="flex flex-col items-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-soft">
                  <step.icon className="h-6 w-6" />
                </div>
                <p className="mt-2 text-center text-caption font-semibold text-slate-700">
                  {step.label}
                </p>
              </div>
              {i < arr.length - 1 && (
                <div className="mx-1 h-0.5 flex-1 bg-gradient-to-r from-brand-300 to-violet-300" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6 lg:p-8">
          <div className="mb-5 flex items-center gap-2">
            <Layers className="h-5 w-5 text-brand-500" />
            <h2 className="text-heading font-semibold text-slate-900">{t.architecture.systemTitle}</h2>
          </div>
          <pre className="overflow-x-auto rounded-xl bg-slate-900 p-5 text-xs leading-relaxed text-slate-100 shadow-inner">
{`┌──────────────┐   REST    ┌─────────────────┐
│ React + Vite │ ◄───────► │ FastAPI + SQLite│
│ Tailwind UI  │           │ CV · Match · Mail│
└──────────────┘           └────────┬────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
               OpenAI API     Gemini API       Mock (demo)`}
          </pre>
        </div>

        <div className="card p-6 lg:p-8">
          <div className="mb-5 flex items-center gap-2">
            <Server className="h-5 w-5 text-brand-500" />
            <h2 className="text-heading font-semibold text-slate-900">{t.architecture.aiTitle}</h2>
          </div>
          <ol className="space-y-4 text-sm text-slate-600">
            {t.architecture.aiSteps.map((step, i) => (
              <li key={i} className="flex gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
                  {i + 1}
                </span>
                <span className="pt-0.5 leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
        </div>

        <div className="card p-6 lg:col-span-2 lg:p-8">
          <h2 className="mb-5 text-heading font-semibold text-slate-900">{t.architecture.stackTitle}</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {stack.map((item) => (
              <div
                key={item.name}
                className="rounded-xl border border-slate-200/80 bg-slate-50/50 px-4 py-3.5 transition hover:border-brand-200 hover:bg-brand-50/30 hover:shadow-sm"
              >
                <p className="font-semibold text-slate-900">{item.name}</p>
                <p className="mt-0.5 text-caption text-slate-500">{item.role}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6 lg:col-span-2 lg:p-8">
          <h2 className="mb-3 text-heading font-semibold text-slate-900">{t.architecture.mockTitle}</h2>
          <p className="text-body-lg leading-relaxed text-slate-600">{t.architecture.mockDesc}</p>
        </div>
      </div>
    </div>
  )
}
