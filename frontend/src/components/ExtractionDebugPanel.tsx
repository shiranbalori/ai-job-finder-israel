import { useState } from 'react'

import { ChevronDown, ChevronUp } from 'lucide-react'

import type { CVUploadResponse, ExtractionDebug, SkillConfidence } from '../api/client'

import { useApp } from '../context/AppContext'



const SHOW_DEBUG =

  import.meta.env.VITE_SHOW_UPLOAD_DEBUG === 'true' || import.meta.env.VITE_SHOW_UPLOAD_DEBUG === '1'



interface Props {

  response: Pick<

    CVUploadResponse,

    'cv_profile' | 'skills_confidence' | 'extraction_debug' | 'extraction_method'

  >

  skillsConfidence?: SkillConfidence[]

}



/** Optional debug panel — hidden unless VITE_SHOW_UPLOAD_DEBUG=true. */

export default function ExtractionDebugPanel({ response, skillsConfidence }: Props) {

  const { t } = useApp()

  const [open, setOpen] = useState(false)



  if (!SHOW_DEBUG) return null



  const debug = response.extraction_debug

  const confidence = skillsConfidence ?? response.skills_confidence ?? response.cv_profile.skills_confidence ?? []



  const payload = {

    extraction_method: response.extraction_method ?? response.cv_profile.extraction_method,

    cv_profile_skills: response.cv_profile.skills,

    skills_confidence: confidence,

    extraction_debug: debug,

  }



  return (

    <div className="rounded-xl border border-amber-200/80 bg-amber-50/40 p-4">

      <button

        type="button"

        className="flex w-full items-center justify-between gap-2 text-sm font-semibold text-amber-900"

        onClick={() => setOpen((v) => !v)}

      >

        <span>{t.upload.showDebugPanel}</span>

        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}

      </button>



      {open && (

        <div className="mt-4 space-y-4 text-xs">

          <DebugSection title={t.upload.debugApiSkills} items={response.cv_profile.skills} />

          <DebugSection

            title={t.upload.debugConfidence}

            items={confidence.map((s) => `${s.skill} (${Math.round(s.confidence * 100)}%, ${s.method})`)}

          />

          {debug && <DebugBlock label={t.upload.debugHeuristic} debug={debug} />}

          <div>

            <p className="mb-1 font-semibold uppercase tracking-wide text-amber-800/80">

              {t.upload.debugRawPayload}

            </p>

            <pre className="max-h-72 overflow-auto rounded-lg bg-slate-900 p-3 text-[11px] leading-relaxed text-slate-100 whitespace-pre-wrap">

              {JSON.stringify(payload, null, 2)}

            </pre>

          </div>

        </div>

      )}

    </div>

  )

}



function DebugSection({ title, items }: { title: string; items: string[] }) {

  return (

    <div>

      <p className="mb-1 font-semibold uppercase tracking-wide text-amber-800/80">

        {title} ({items.length})

      </p>

      <div className="flex flex-wrap gap-1.5">

        {items.length ? (

          items.map((item) => (

            <span key={item} className="rounded-md bg-white px-2 py-0.5 text-slate-700 ring-1 ring-amber-200">

              {item}

            </span>

          ))

        ) : (

          <span className="text-slate-500">—</span>

        )}

      </div>

    </div>

  )

}



function DebugBlock({ label, debug }: { label: string; debug: ExtractionDebug }) {

  return (

    <div className="grid gap-3 sm:grid-cols-2">

      <PipelineList title={`${label} — regex`} items={debug.raw_regex ?? []} />

      <PipelineList title={`${label} — keyword`} items={debug.raw_keyword} />

      <PipelineList title={`${label} — fuzzy`} items={debug.raw_fuzzy ?? []} />

      <PipelineList title={`${label} — semantic`} items={debug.raw_semantic} />

      <PipelineList title={`${label} — heuristic`} items={debug.raw_heuristic ?? []} />

      <PipelineList title={`${label} — merged`} items={debug.merged ?? debug.merged_skills} />

      <PipelineList title={`${label} — filtered out`} items={debug.filtered_out} />

      {debug.priority_missing.length > 0 && (

        <PipelineList title={`${label} — priority missing`} items={debug.priority_missing} />

      )}

    </div>

  )

}



function PipelineList({ title, items }: { title: string; items: string[] }) {

  return (

    <div className="rounded-lg bg-white/70 p-2 ring-1 ring-amber-100">

      <p className="mb-1 font-medium text-amber-900">{title}</p>

      <p className="text-slate-600">{items.length ? items.join(', ') : '—'}</p>

    </div>

  )

}


