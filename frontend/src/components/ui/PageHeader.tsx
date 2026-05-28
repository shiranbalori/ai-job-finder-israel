interface Props {
  title: string
  subtitle?: string
  badge?: string
  children?: React.ReactNode
}

export default function PageHeader({ title, subtitle, badge, children }: Props) {
  return (
    <header className="mb-8 border-b border-slate-200/60 pb-8 lg:mb-10 lg:pb-10">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl">
          {badge && (
            <span className="badge-brand mb-4 inline-flex">{badge}</span>
          )}
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-[2.5rem]">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-3 text-body-lg leading-relaxed text-slate-600">{subtitle}</p>
          )}
        </div>
        {children && (
          <div className="flex shrink-0 flex-wrap items-center gap-2 sm:gap-3">{children}</div>
        )}
      </div>
    </header>
  )
}
