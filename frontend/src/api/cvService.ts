/**
 * CV API service — Real Mode upload flow.
 */

import { liveApi, type CVUploadResponse } from './client'
import { backendUnreachableHint } from './config'

export type { CVUploadResponse }

export const UPLOAD_SLOW_MS = 20_000
export const UPLOAD_TIMEOUT_MS = 90_000

const USE_MOCK =
  import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === '1'

export class CVUploadError extends Error {
  constructor(
    message: string,
    readonly code: 'offline' | 'mock_only' | 'validation' | 'timeout' | 'unknown' = 'unknown',
  ) {
    super(message)
    this.name = 'CVUploadError'
  }
}

async function pingBackend(): Promise<boolean> {
  if (USE_MOCK) return false
  try {
    const h = await liveApi.health()
    return h.status === 'ok' || h.status === 'degraded'
  } catch {
    return false
  }
}

function classifyError(err: unknown): CVUploadError {
  if (err instanceof CVUploadError) return err

  const msg = err instanceof Error ? err.message : 'Upload failed'

  if (err instanceof DOMException && err.name === 'AbortError') {
    return new CVUploadError(
      'Upload timed out after 90 seconds. Try a smaller PDF or retry when the backend is less busy.',
      'timeout',
    )
  }

  if (msg.includes('VITE_USE_MOCK') || msg.includes('Real upload requires')) {
    return new CVUploadError(
      'Real Mode is disabled. Set VITE_USE_MOCK=false in frontend/.env and restart the dev server.',
      'mock_only',
    )
  }

  if (
    msg.includes('Failed to fetch') ||
    msg.includes('NetworkError') ||
    msg.includes('ERR_CONNECTION_REFUSED')
  ) {
    return new CVUploadError(backendUnreachableHint(), 'offline')
  }

  if (
    msg.includes('Only PDF') ||
    msg.includes('File too large') ||
    msg.includes('Could not extract text') ||
    msg.includes('.doc format')
  ) {
    return new CVUploadError(msg, 'validation')
  }

  return new CVUploadError(msg, 'unknown')
}

export async function uploadRealCV(file: File): Promise<CVUploadResponse> {
  if (USE_MOCK) {
    throw new CVUploadError(
      'Real upload requires VITE_USE_MOCK=false. Demo Mode still works via the Demo button.',
      'mock_only',
    )
  }

  const online = await pingBackend()
  if (!online) {
    throw new CVUploadError(backendUnreachableHint(), 'offline')
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT_MS)

  try {
    return await liveApi.uploadCV(file, controller.signal)
  } catch (err) {
    throw classifyError(err)
  } finally {
    clearTimeout(timer)
  }
}

export function validateCVFile(file: File): string | null {
  const name = file.name.toLowerCase()
  if (!name.endsWith('.pdf') && !name.endsWith('.docx')) {
    return 'Please upload PDF or DOCX only (.doc is not supported).'
  }
  const maxMb = 10
  if (file.size > maxMb * 1024 * 1024) {
    return `File too large. Maximum size is ${maxMb} MB.`
  }
  return null
}
