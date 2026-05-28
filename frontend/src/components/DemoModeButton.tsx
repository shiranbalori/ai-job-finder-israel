import { Loader2, Play, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../context/AppContext'

interface Props {
  size?: 'default' | 'large'
  navigateToDashboard?: boolean
  className?: string
}

/** Full Demo Mode — fake CV, Israeli jobs, curated match scores. No API keys or upload. */
export default function DemoModeButton({
  size = 'default',
  navigateToDashboard = true,
  className = '',
}: Props) {
  const { t, demoLoading, demoMode, activateDemo } = useApp()
  const navigate = useNavigate()

  const handleClick = async () => {
    if (demoMode && navigateToDashboard) {
      navigate('/dashboard')
      return
    }
    await activateDemo()
    if (navigateToDashboard) navigate('/dashboard')
  }

  const isLarge = size === 'large'

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={demoLoading}
      className={`${isLarge ? 'btn-demo min-w-[220px] px-8 py-4 text-base' : 'btn-demo'} ${
        demoMode ? '!border-emerald-400 !bg-emerald-50 !text-emerald-700' : ''
      } ${className}`}
    >
      {demoLoading ? (
        <>
          <Loader2 className={`animate-spin ${isLarge ? 'h-5 w-5' : 'h-4 w-4'}`} />
          {t.demo.loading}
        </>
      ) : demoMode ? (
        <>
          <Sparkles className={isLarge ? 'h-5 w-5' : 'h-4 w-4'} />
          {t.demo.viewDashboard}
        </>
      ) : (
        <>
          <Play className={`fill-current ${isLarge ? 'h-5 w-5' : 'h-4 w-4'}`} />
          {t.demo.activate}
        </>
      )}
    </button>
  )
}
