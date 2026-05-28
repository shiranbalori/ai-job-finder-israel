import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Mail,
  Sparkles,
  Target,
  Upload,
  Zap,
} from 'lucide-react'
import { api } from '../api'
import { useApp } from '../context/AppContext'
import DemoModeButton from '../components/DemoModeButton'

const steps = [
  { icon: Upload, key: 'upload' },
  { icon: Brain, key: 'analyze' },
  { icon: Target, key: 'match' },
  { icon: Mail, key: 'digest' },
] as const

export default function LandingPage() {
  const { t } = useApp()
  const companies = api.getCompanies()

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute -top-24 left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-brand-400/20 blur-3xl" />
        <div className="absolute top-32 end-0 h-64 w-64 rounded-full bg-violet-400/15 blur-3xl" />

        <div className="page-container relative pb-8 pt-12 sm:pt-20">
          <div className="mx-auto max-w-4xl text-center">
            <span className="inline-flex animate-slide-up items-center gap-2 rounded-full border border-brand-200/80 bg-white/80 px-4 py-1.5 text-xs font-bold uppercase tracking-wide text-brand-700 shadow-sm backdrop-blur">
              <Zap className="h-3.5 w-3.5" />
              AI · Data · Automation · Israel
            </span>

            <h1 className="mt-8 animate-slide-up text-4xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-5xl lg:text-6xl [animation-delay:0.1s]">
              {t.landing.heroTitleBefore}{' '}
              <span className="gradient-text">{t.landing.heroTitleHighlight}</span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl animate-slide-up text-lg text-slate-600 sm:text-xl [animation-delay:0.15s]">
              {t.landing.heroSubtitle}
            </p>

            {/* Primary CTAs — Demo Mode prominent */}
            <div className="mt-10 flex animate-slide-up flex-col items-center justify-center gap-4 sm:flex-row [animation-delay:0.2s]">
              <DemoModeButton size="large" />
              <Link to="/upload" className="btn-primary w-full sm:w-auto">
                <Upload className="h-5 w-5" />
                {t.landing.ctaUpload}
              </Link>
            </div>

            <p className="mt-4 flex animate-slide-up items-center justify-center gap-2 text-sm text-slate-500 [animation-delay:0.25s]">
              <Sparkles className="h-4 w-4 text-violet-500" />
              {t.landing.demoHint}
            </p>
          </div>

          {/* Stats strip */}
          <div className="stagger mx-auto mt-16 grid max-w-3xl gap-4 sm:grid-cols-3">
            {t.landing.stats.map((s) => (
              <div key={s.label} className="card-glass text-center">
                <p className="text-2xl font-bold gradient-text">{s.value}</p>
                <p className="mt-1 text-sm text-slate-600">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Company strip */}
      <section className="border-y border-slate-100 bg-white/60 py-8">
        <div className="page-container !py-0">
          <p className="mb-4 text-center text-xs font-semibold uppercase tracking-widest text-slate-400">
            {t.landing.companiesTitle}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
            {companies.map((name) => (
              <span key={name} className="text-sm font-semibold text-slate-400 transition hover:text-brand-600">
                {name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="page-container">
        <div className="grid gap-6 md:grid-cols-3">
          {t.landing.features.map((f, i) => {
            const icons = [Brain, Target, Mail]
            const Icon = icons[i]
            return (
              <div
                key={f.title}
                className="card group transition hover:-translate-y-1 hover:shadow-soft"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-soft transition group-hover:shadow-glow">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.desc}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* How it works preview */}
      <section className="bg-slate-50/80 py-16">
        <div className="page-container">
          <h2 className="text-center text-2xl font-bold text-slate-900">{t.landing.howTitle}</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((step, i) => {
              const Icon = step.icon
              const copy = t.landing.steps[step.key]
              return (
                <div key={step.key} className="relative text-center">
                  {i < steps.length - 1 && (
                    <div className="absolute top-6 hidden h-0.5 w-full bg-gradient-to-r from-brand-200 to-transparent lg:block start-1/2" />
                  )}
                  <div className="relative mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-brand-600 shadow-card ring-4 ring-slate-50">
                    <Icon className="h-6 w-6" />
                  </div>
                  <p className="mt-2 text-xs font-bold text-brand-600">Step {i + 1}</p>
                  <h3 className="mt-1 font-semibold text-slate-900">{copy.title}</h3>
                  <p className="mt-1 text-sm text-slate-500">{copy.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Interview CTA */}
      <section className="page-container">
        <div className="overflow-hidden rounded-3xl bg-gradient-brand p-8 text-white shadow-glow sm:p-12">
          <div className="flex flex-col items-center gap-6 text-center lg:flex-row lg:text-start">
            <div className="flex-1">
              <h2 className="text-2xl font-bold sm:text-3xl">{t.landing.ctaBlockTitle}</h2>
              <p className="mt-3 text-brand-100">{t.landing.ctaBlockDesc}</p>
              <ul className="mt-6 space-y-2 text-sm text-white/90">
                {t.landing.ctaBullets.map((b) => (
                  <li key={b} className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                    {b}
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
              <DemoModeButton
                size="large"
                className="!border-white/30 !bg-white !text-brand-700 !shadow-lg hover:!bg-brand-50"
              />
              <Link
                to="/architecture"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                {t.nav.architecture}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
