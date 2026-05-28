import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, LogOut, Settings } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'

export default function UserMenu() {
  const { t } = useApp()
  const { user, isAuthenticated, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  if (!isAuthenticated || !user) {
    return (
      <div className="hidden items-center gap-2 sm:flex">
        <Link to="/login" className="btn-ghost btn-sm">
          {t.auth.loginAction}
        </Link>
        <Link to="/register" className="btn-primary btn-sm">
          {t.auth.signUpLink}
        </Link>
      </div>
    )
  }

  const initials = (user.full_name || user.email).charAt(0).toUpperCase()

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        className="flex items-center gap-2 rounded-xl border border-slate-200/80 bg-white px-2 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-brand-200 hover:bg-brand-50/50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-brand-700"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-brand text-xs font-bold text-white">
          {initials}
        </span>
        <span className="hidden max-w-[8rem] truncate md:inline">{user.full_name || user.email}</span>
        <ChevronDown className={`h-4 w-4 text-slate-400 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute end-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border border-slate-200/80 bg-white py-1 shadow-lg dark:border-slate-600 dark:bg-slate-800">
          <div className="border-b border-slate-100 px-4 py-3 dark:border-slate-700">
            <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
              {user.full_name || user.email.split('@')[0]}
            </p>
            <p className="truncate text-caption text-slate-500">{user.email}</p>
          </div>
          <Link
            to="/settings"
            className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-700/50"
            onClick={() => setOpen(false)}
          >
            <Settings className="h-4 w-4" />
            {t.nav.settings}
          </Link>
          <button
            type="button"
            className="flex w-full items-center gap-2 px-4 py-2.5 text-start text-sm text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/30"
            onClick={() => {
              setOpen(false)
              void logout()
            }}
          >
            <LogOut className="h-4 w-4" />
            {t.auth.logout}
          </button>
        </div>
      )}
    </div>
  )
}
