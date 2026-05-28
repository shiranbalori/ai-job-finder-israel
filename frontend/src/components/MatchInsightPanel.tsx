import type { JobMatch, JobSkillsDebug, ScoreBreakdown } from '../api/client'
import { useApp } from '../context/AppContext'

interface Props {
  match: Pick<
    JobMatch,
    | 'match_score'
    | 'match_reason'
    | 'matched_skills'
    | 'missing_skills'
    | 'semantic_matches'
    | 'job_skills_extracted'
    | 'job_skills_debug'
    | 'score_breakdown'
    | 'semantic_overlap'
  >
  scoreLabel?: string
  compact?: boolean
  showDebug?: boolean
}

function BreakdownBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-800">{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function JobSkillsDebugPanel({ debug, extracted }: { debug?: JobSkillsDebug | null; extracted?: string[] }) {
  const { t } = useApp()
  const skills = extracted?.length ? extracted : debug?.final_skills ?? []
  if (!skills.length && !debug) return null

  return (
    <div className="rounded-lg border border-slate-200 bg-white/80 p-3 text-xs">
      <p className="font-semibold uppercase tracking-wide text-slate-500">{t.job.jobSkillsDebug}</p>
      <p className="mt-1 text-slate-600">
        {t.job.jobSkillsExtracted}: {skills.join(', ') || '—'}
      </p>
      {debug && (
        <div className="mt-2 grid gap-1 text-slate-500">
          {debug.raw_regex?.length ? <p>regex: {debug.raw_regex.join(', ')}</p> : null}
          {debug.raw_keyword?.length ? <p>keyword: {debug.raw_keyword.join(', ')}</p> : null}
          {debug.title_inferred?.length ? <p>title: {debug.title_inferred.join(', ')}</p> : null}
        </div>
      )}
    </div>
  )
}

export default function MatchInsightPanel({
  match,
  scoreLabel,
  compact = false,
  showDebug = true,
}: Props) {
  const { t } = useApp()
  const breakdown: ScoreBreakdown | null | undefined = match.score_breakdown
  const semanticPct = Math.round((match.semantic_overlap ?? 0) * 100)
  const semanticMatches = match.semantic_matches ?? []

  return (
    <div className={compact ? 'space-y-4' : 'space-y-6'}>
      {scoreLabel && (
        <p className="text-center text-lg font-bold text-slate-900">{scoreLabel}</p>
      )}

      <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {t.job.whyMatch}
        </p>
        <p className="mt-2 text-sm leading-relaxed text-slate-700">{match.match_reason}</p>
        {semanticPct > 0 && (
          <p className="mt-2 text-xs text-brand-700">
            {t.job.semanticOverlap}: <span className="font-semibold">{semanticPct}%</span>
          </p>
        )}
      </div>

      {breakdown && (
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            {t.job.scoreBreakdown}
          </p>
          <BreakdownBar label={t.job.breakdownSkills} value={breakdown.skills} max={30} color="bg-emerald-500" />
          <BreakdownBar
            label={t.job.breakdownSemantic}
            value={breakdown.semantic}
            max={25}
            color="bg-brand-500"
          />
          {(breakdown.embedding ?? 0) > 0 && (
            <BreakdownBar
              label={t.job.breakdownEmbedding}
              value={breakdown.embedding ?? 0}
              max={20}
              color="bg-indigo-500"
            />
          )}
          <BreakdownBar label={t.job.breakdownTitle} value={breakdown.title} max={15} color="bg-violet-500" />
          <BreakdownBar label={t.job.breakdownExperience} value={breakdown.experience} max={10} color="bg-amber-500" />
          {(breakdown.domain ?? 0) > 0 && (
            <BreakdownBar label={t.job.breakdownDomain} value={breakdown.domain ?? 0} max={5} color="bg-cyan-500" />
          )}
        </div>
      )}

      <div>
        <p className="text-sm font-semibold text-emerald-800">{t.job.matchedSkills}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {match.matched_skills.length ? (
            match.matched_skills.map((s) => (
              <span key={s} className="badge-success">
                {s}
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-500">{t.job.noMatchedYet}</span>
          )}
        </div>
      </div>

      {semanticMatches.length > 0 && (
        <div>
          <p className="text-sm font-semibold text-brand-800">{t.job.semanticMatches}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {semanticMatches.map((s) => (
              <span key={s} className="badge-brand">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="text-sm font-semibold text-amber-800">{t.job.missingSkills}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {match.missing_skills.length ? (
            match.missing_skills.map((s) => (
              <span key={s} className="badge-warning">
                {s}
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-500">{t.job.noGaps}</span>
          )}
        </div>
      </div>

      {showDebug && (match.job_skills_debug || match.job_skills_extracted?.length) ? (
        <JobSkillsDebugPanel debug={match.job_skills_debug} extracted={match.job_skills_extracted} />
      ) : null}
    </div>
  )
}

export function SkillConfidenceList({ skills }: { skills: import('../api/client').SkillConfidence[] }) {
  const { t } = useApp()
  if (!skills.length) return null

  return (
    <div>
      <p className="text-overline uppercase text-slate-500">
        {t.upload.skillsConfidenceLabel} ({skills.length})
      </p>
      <div className="mt-2 space-y-2">
        {skills.map((s) => (
          <div key={s.skill} className="flex items-center gap-3">
            <span className="w-28 shrink-0 truncate text-sm font-medium text-slate-800">{s.skill}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
                style={{ width: `${Math.round(s.confidence * 100)}%` }}
              />
            </div>
            <span className="w-10 shrink-0 text-right text-caption text-slate-500">
              {Math.round(s.confidence * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
