/** Company avatar — gradient initials with optional logo attempt. */

interface Props {
  company: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizes = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-11 w-11 text-sm',
  lg: 'h-14 w-14 text-base',
}

function hashColor(name: string): string {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  const hues = [250, 265, 280, 210, 190, 330]
  const hue = hues[Math.abs(hash) % hues.length]
  return `linear-gradient(135deg, hsl(${hue} 70% 52%), hsl(${hue + 25} 65% 42%))`
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}

export default function CompanyLogo({ company, size = 'md', className = '' }: Props) {
  const bg = hashColor(company)

  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-xl font-bold text-white shadow-soft ring-2 ring-white/20 dark:ring-slate-700/50 ${sizes[size]} ${className}`}
      style={{ background: bg }}
      title={company}
      aria-hidden
    >
      {initials(company)}
    </div>
  )
}
