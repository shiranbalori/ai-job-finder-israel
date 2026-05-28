import { NavLink } from 'react-router-dom'
import { Briefcase, Home, LayoutDashboard, Settings, Upload } from 'lucide-react'
import { useApp } from '../context/AppContext'

const tabs = [
  { to: '/', icon: Home, labelKey: 'home' as const, end: true },
  { to: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' as const },
  { to: '/upload', icon: Upload, labelKey: 'upload' as const },
  { to: '/settings', icon: Settings, labelKey: 'settings' as const },
  { to: '/architecture', icon: Briefcase, labelKey: 'architecture' as const },
]

export default function MobileNav() {
  const { t } = useApp()

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200/80 bg-white/90 px-2 pb-[env(safe-area-inset-bottom)] pt-2 backdrop-blur-xl md:hidden"
      aria-label="Mobile navigation"
    >
      <div className="mx-auto flex max-w-lg justify-around">
        {tabs.map(({ to, icon: Icon, labelKey, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex min-w-[3.5rem] flex-col items-center gap-0.5 rounded-xl px-2 py-1.5 text-[10px] font-medium transition ${
                isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-500 active:bg-slate-100'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className="h-5 w-5" strokeWidth={isActive ? 2.25 : 2} />
                <span className="truncate">{t.nav[labelKey]}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
