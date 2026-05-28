import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface Props {
  icon?: LucideIcon
  title: string
  description?: string
  action?: ReactNode
  variant?: 'default' | 'compact'
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  variant = 'default',
}: Props) {
  const isCompact = variant === 'compact'

  return (
    <div
      className={`flex flex-col items-center text-center ${
        isCompact ? 'py-12' : 'card py-16 lg:py-20'
      }`}
    >
      <div
        className={`mb-5 flex items-center justify-center rounded-2xl bg-gradient-to-br from-slate-100 to-slate-50 ring-1 ring-slate-200/60 ${
          isCompact ? 'h-12 w-12' : 'h-16 w-16'
        }`}
      >
        {Icon ? (
          <Icon className={`text-slate-400 ${isCompact ? 'h-6 w-6' : 'h-8 w-8'}`} />
        ) : (
          <svg
            className={`text-slate-300 ${isCompact ? 'h-6 w-6' : 'h-8 w-8'}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        )}
      </div>
      <h3 className={`font-semibold text-slate-900 ${isCompact ? 'text-base' : 'text-lg'}`}>
        {title}
      </h3>
      {description && (
        <p className={`mt-2 max-w-md text-slate-500 ${isCompact ? 'text-sm' : 'text-body-lg'}`}>
          {description}
        </p>
      )}
      {action && <div className="mt-8 flex flex-wrap justify-center gap-3">{action}</div>}
    </div>
  )
}
