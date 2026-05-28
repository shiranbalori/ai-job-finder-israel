import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus, Mail, Lock, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'
import PageHeader from '../components/ui/PageHeader'

export default function RegisterPage() {
  const { t } = useApp()
  const { register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register(email, password, fullName || undefined)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : t.auth.registerFailed)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-container">
      <div className="mx-auto max-w-md">
        <PageHeader title={t.auth.registerTitle} subtitle={t.auth.registerSubtitle} />
        <form onSubmit={submit} className="card space-y-5 p-6 lg:p-8">
          <div>
            <label className="label flex items-center gap-2">
              <User className="h-4 w-4 text-slate-400" />
              {t.auth.fullName}
            </label>
            <input
              className="input"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={t.auth.fullNamePlaceholder}
            />
          </div>
          <div>
            <label className="label flex items-center gap-2">
              <Mail className="h-4 w-4 text-slate-400" />
              {t.auth.email}
            </label>
            <input className="input" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="label flex items-center gap-2">
              <Lock className="h-4 w-4 text-slate-400" />
              {t.auth.password}
            </label>
            <input
              className="input"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <p className="mt-1 text-caption text-slate-500">{t.auth.passwordHint}</p>
          </div>
          {error && (
            <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200">
              {error}
            </p>
          )}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            <UserPlus className="h-4 w-4" />
            {loading ? t.loading : t.auth.registerAction}
          </button>
          <p className="text-center text-sm text-slate-600 dark:text-slate-400">
            {t.auth.hasAccount}{' '}
            <Link to="/login" className="font-semibold text-brand-600 hover:underline dark:text-brand-400">
              {t.auth.loginLink}
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
