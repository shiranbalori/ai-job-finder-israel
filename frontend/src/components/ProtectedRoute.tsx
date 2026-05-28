import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'
import LoadingState from './LoadingState'

interface Props {
  /** Allow demo mode users through without login */
  allowDemo?: boolean
}

export default function ProtectedRoute({ allowDemo = true }: Props) {
  const { isAuthenticated, loading } = useAuth()
  const { demoMode } = useApp()
  const location = useLocation()

  if (loading) return <LoadingState message="Checking session…" />

  if (isAuthenticated || (allowDemo && demoMode)) {
    return <Outlet />
  }

  return <Navigate to="/login" state={{ from: location.pathname }} replace />
}
