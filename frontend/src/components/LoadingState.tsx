import { Loader2 } from 'lucide-react'
import { useApp } from '../context/AppContext'
import DashboardSkeleton from './ui/DashboardSkeleton'

interface Props {
  message?: string
  variant?: 'spinner' | 'dashboard'
}

export default function LoadingState({ message, variant = 'spinner' }: Props) {
  const { t } = useApp()

  if (variant === 'dashboard') {
    return <DashboardSkeleton />
  }

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-5 px-4">
      <div className="relative">
        <div className="absolute inset-0 animate-pulse-soft rounded-full bg-brand-400/25 blur-2xl" />
        <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-card ring-1 ring-slate-200/80">
          <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
        </div>
      </div>
      <div className="max-w-sm text-center">
        <p className="text-base font-medium text-slate-800">{message || t.loading}</p>
        <p className="mt-1.5 text-sm text-slate-500">{t.loadingHint}</p>
        <div className="mx-auto mt-4 h-1 w-32 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full w-1/2 animate-pulse rounded-full bg-brand-400" />
        </div>
      </div>
    </div>
  )
}
