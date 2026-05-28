import { Cloud, CloudOff, Database } from 'lucide-react'
import { useApp } from '../context/AppContext'

export default function BackendStatus() {
  const { backendOnline, usingMock } = useApp()

  if (usingMock) {
    return (
      <span className="badge-warning inline-flex items-center gap-1.5 px-3 py-1.5">
        <Database className="h-3.5 w-3.5" />
        Offline mock
      </span>
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ${
        backendOnline
          ? 'bg-emerald-50 text-emerald-800 ring-emerald-100'
          : 'bg-red-50 text-red-800 ring-red-100'
      }`}
    >
      {backendOnline ? (
        <>
          <Cloud className="h-3.5 w-3.5" />
          Live API
        </>
      ) : (
        <>
          <CloudOff className="h-3.5 w-3.5" />
          Offline
        </>
      )}
    </span>
  )
}
