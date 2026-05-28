/** Dashboard skeleton — polished loading placeholder */
export default function DashboardSkeleton() {
  return (
    <div className="page-container animate-fade-in">
      <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-3">
          <div className="skeleton-shimmer h-4 w-24" />
          <div className="skeleton-shimmer h-9 w-64 max-w-full" />
          <div className="skeleton-shimmer h-4 w-96 max-w-full" />
        </div>
        <div className="flex gap-2">
          <div className="skeleton-shimmer h-10 w-32 rounded-xl" />
          <div className="skeleton-shimmer h-10 w-36 rounded-xl" />
        </div>
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card p-5">
            <div className="flex justify-between">
              <div className="space-y-2">
                <div className="skeleton-shimmer h-3 w-20" />
                <div className="skeleton-shimmer h-8 w-16" />
              </div>
              <div className="skeleton-shimmer h-11 w-11 rounded-xl" />
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <div className="space-y-4">
          <div className="card h-48" />
          <div className="card h-64" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card space-y-4 p-5">
              <div className="flex justify-between">
                <div className="skeleton-shimmer h-5 w-3/4" />
                <div className="skeleton-shimmer h-14 w-14 rounded-full" />
              </div>
              <div className="skeleton-shimmer h-3 w-full" />
              <div className="skeleton-shimmer h-3 w-5/6" />
              <div className="flex gap-2">
                <div className="skeleton-shimmer h-6 w-16 rounded-full" />
                <div className="skeleton-shimmer h-6 w-16 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
