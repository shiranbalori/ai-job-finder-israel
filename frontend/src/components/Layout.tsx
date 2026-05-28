import { Link, NavLink, Outlet } from 'react-router-dom'

import { Briefcase, Menu, Moon, Sun, X } from 'lucide-react'

import { useState } from 'react'

import { useApp } from '../context/AppContext'

import { useTheme } from '../context/ThemeContext'

import DemoModeButton from './DemoModeButton'

import MobileNav from './MobileNav'

import PwaInstallPrompt from './PwaInstallPrompt'

import UserMenu from './UserMenu'

import DemoModeOverlay from './demo/DemoModeOverlay'

import DemoBanner from './demo/DemoBanner'



export default function Layout() {

  const { t, dir, lang, setLang, demoMode } = useApp()

  const { theme, toggleTheme } = useTheme()

  const [menuOpen, setMenuOpen] = useState(false)



  const navClass = ({ isActive }: { isActive: boolean }) =>

    isActive ? 'nav-link nav-link-active' : 'nav-link'



  return (

    <div

      dir={dir}

      className="min-h-screen bg-mesh pb-[calc(4.5rem+env(safe-area-inset-bottom))] transition-colors duration-300 dark:bg-mesh-dark md:pb-0"

    >

      <header className="sticky top-0 z-50 border-b border-slate-200/60 bg-white/85 shadow-nav backdrop-blur-xl backdrop-saturate-150 dark:border-slate-700/60 dark:bg-slate-900/85">

        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">

          <Link to="/" className="flex items-center gap-3 transition-opacity hover:opacity-90">

            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-brand text-white shadow-soft ring-1 ring-white/20">

              <Briefcase className="h-5 w-5" strokeWidth={2.25} />

            </span>

            <div className="hidden sm:block">

              <span className="block text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100">

                {t.appName}

              </span>

              <span className="text-caption text-slate-500 dark:text-slate-400">{t.tagline}</span>

            </div>

          </Link>



          <nav className="hidden items-center gap-0.5 lg:flex">

            <NavLink to="/" className={navClass} end>

              {t.nav.home}

            </NavLink>

            <NavLink to="/dashboard" className={navClass}>

              {t.nav.dashboard}

            </NavLink>

            <NavLink to="/upload" className={navClass}>

              {t.nav.upload}

            </NavLink>

            <NavLink to="/settings" className={navClass}>

              {t.nav.settings}

            </NavLink>

            <NavLink to="/architecture" className={navClass}>

              {t.nav.architecture}

            </NavLink>

          </nav>



          <div className="flex items-center gap-2">

            {demoMode && (

              <span className="badge-success hidden sm:inline-flex">Demo</span>

            )}

            <button

              type="button"

              className="btn-ghost !p-2"

              onClick={toggleTheme}

              aria-label={theme === 'dark' ? 'Light mode' : 'Dark mode'}

            >

              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}

            </button>

            <select

              className="input w-auto !py-1.5 !text-xs font-medium"

              value={lang}

              onChange={(e) => setLang(e.target.value as 'en' | 'he')}

              aria-label="Language"

            >

              <option value="en">EN</option>

              <option value="he">עב</option>

            </select>

            <div className="hidden md:block">

              <DemoModeButton />

            </div>

            <UserMenu />

            <button

              type="button"

              className="btn-ghost !p-2 lg:hidden"

              onClick={() => setMenuOpen(!menuOpen)}

              aria-label="Menu"

            >

              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}

            </button>

          </div>

        </div>



        {menuOpen && (

          <div className="border-t border-slate-100 bg-white px-4 py-4 dark:border-slate-700 dark:bg-slate-900 lg:hidden">

            <nav className="flex flex-col gap-1">

              <NavLink to="/" className={navClass} end onClick={() => setMenuOpen(false)}>

                {t.nav.home}

              </NavLink>

              <NavLink to="/dashboard" className={navClass} onClick={() => setMenuOpen(false)}>

                {t.nav.dashboard}

              </NavLink>

              <NavLink to="/upload" className={navClass} onClick={() => setMenuOpen(false)}>

                {t.nav.upload}

              </NavLink>

              <NavLink to="/settings" className={navClass} onClick={() => setMenuOpen(false)}>

                {t.nav.settings}

              </NavLink>

            </nav>

            <div className="mt-4 border-t border-slate-100 pt-4 dark:border-slate-700">

              <DemoModeButton className="w-full" />

            </div>

          </div>

        )}

      </header>



      <DemoBanner />

      <DemoModeOverlay />



      <main className="animate-fade-in">

        <Outlet />

      </main>



      <footer className="mt-24 hidden border-t border-slate-200/60 bg-white/60 py-12 dark:border-slate-700 dark:bg-slate-900/60 md:block">

        <div className="mx-auto max-w-7xl px-6 text-center lg:px-8">

          <p className="text-sm text-slate-500 dark:text-slate-400">

            © {new Date().getFullYear()} AI Job Finder Israel

          </p>

          <p className="mt-1 text-caption text-slate-400">Portfolio · AI job matching for Israel</p>

        </div>

      </footer>



      <MobileNav />

      <PwaInstallPrompt />

    </div>

  )

}

