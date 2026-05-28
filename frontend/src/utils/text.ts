const CORP_SUFFIX = /^(ltd|inc|corp|llc|co|gmbh|plc)\.?$/i

/** Strip HTML and normalize skill labels for display. */
export function sanitizeSkillLabel(raw: string | null | undefined): string {
  if (!raw) return ''
  let text = raw.replace(/<[^>]*>/gi, ' ')
  text = text.replace(/\s+/g, ' ').trim()
  text = text.replace(/^At\s+/i, '')

  const words = text.split(/\s+/).filter(Boolean)
  if (words.length > 2) {
    text = words[0].replace(/[.,;:]+$/, '')
  } else if (words.length === 2) {
    const second = words[1].replace(/[.,;:]+$/, '')
    if (CORP_SUFFIX.test(second) || text.length > 28) {
      text = words[0].replace(/[.,;:]+$/, '')
    }
  }

  return text.replace(/[.,;:…]+$/g, '')
}

/** Pick the first readable skill gap label from dashboard stats. */
export function pickTopSkillGap(skills: string[] | null | undefined): string {
  if (!skills?.length) return '—'
  for (const raw of skills) {
    const cleaned = sanitizeSkillLabel(raw)
    if (!cleaned || cleaned.includes('<') || cleaned.includes('>')) continue
    if (cleaned.length > 48 || cleaned.split(/\s+/).length > 4) continue
    return cleaned
  }
  return '—'
}
