/**
 * API base URL resolution.
 *
 * Production: set VITE_API_URL to your Render backend (e.g. https://api.example.onrender.com).
 * Local dev: leave VITE_API_URL empty — Vite proxies /api and /health to VITE_DEV_API_URL.
 */

function normalizeBase(url: string): string {
  return url.trim().replace(/\/+$/, '')
}

/** Public API origin. Empty string = same-origin (Vite dev proxy). */
export const API_BASE_URL = normalizeBase(
  import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '',
)

/** Build a full API path. Relative when API_BASE_URL is empty (dev proxy). */
export function apiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return API_BASE_URL ? `${API_BASE_URL}${normalized}` : normalized
}

/** User-facing hint when fetch fails (no hardcoded localhost). */
export function backendUnreachableHint(): string {
  if (API_BASE_URL) {
    return `Cannot reach the API at ${API_BASE_URL}. Check that the backend is running.`
  }
  return 'Cannot reach the backend. Start the API server and ensure VITE_DEV_API_URL is set in frontend/.env.development.'
}
