/** Circular match score visualization (0–100). */

interface Props {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

const sizes = {
  sm: { box: 56, stroke: 4, text: 'text-sm' },
  md: { box: 72, stroke: 5, text: 'text-lg' },
  lg: { box: 96, stroke: 6, text: 'text-2xl' },
}

function scoreColor(score: number): string {
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#6366f1'
  if (score >= 40) return '#f59e0b'
  return '#94a3b8'
}

export default function MatchScoreRing({ score, size = 'md' }: Props) {
  const { box, stroke, text } = sizes[size]
  const r = (box - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = c - (score / 100) * c
  const color = scoreColor(score)

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: box, height: box }}
      aria-label={`Match score ${Math.round(score)} percent`}
    >
      <svg width={box} height={box} className="-rotate-90" aria-hidden>
        <circle cx={box / 2} cy={box / 2} r={r} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
        <circle
          cx={box / 2}
          cy={box / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
          style={{ filter: score >= 80 ? 'drop-shadow(0 0 6px rgba(16,185,129,0.35))' : undefined }}
        />
      </svg>
      <span className={`absolute font-bold tabular-nums text-slate-800 ${text}`}>
        {Math.round(score)}
      </span>
    </div>
  )
}
