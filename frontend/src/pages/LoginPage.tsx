import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { LogIn, Mail, Lock, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'
import PageHeader from '../components/ui/PageHeader'

export default function LoginPage() {
  const { t } = useApp()
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from || '/dashboard'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : t.auth.loginFailed)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-container">
      <div className="mx-auto max-w-md">
        <PageHeader title={t.auth.loginTitle} subtitle={t.auth.loginSubtitle} />
        <form onSubmit={submit} className="card space-y-5 p-6 lg:p-8">
          <div>
            <label className="label flex items-center gap-2">
              <Mail className="h-4 w-4 text-slate-400" />
              {t.auth.email}
            </label>
            <input
              className="input"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="label flex items-center gap-2">
              <Lock className="h-4 w-4 text-slate-400" />
              {t.auth.password}
            </label>
            <input
              className="input"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && (
            <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200">
              {error}
            </p>
          )}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            <LogIn className="h-4 w-4" />
            {loading ? t.loading : t.auth.loginAction}
          </button>
          <p className="text-center text-sm text-slate-600 dark:text-slate-400">
            {t.auth.noAccount}{' '}
            <Link to="/register" className="font-semibold text-brand-600 hover:underline dark:text-brand-400">
              {t.auth.signUpLink}
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
