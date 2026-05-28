import { useEffect, useState } from 'react'
import { Download, Share, X } from 'lucide-react'
import { useApp } from '../context/AppContext'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

function isIosSafari() {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent
  return /iPad|iPhone|iPod/.test(ua) && !(window as Window & { MSStream?: unknown }).MSStream
}

function isStandalone() {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  )
}

/** Optional install banner for Add to Home Screen (Android + iOS). */
export default function PwaInstallPrompt() {
  const { t } = useApp()
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [showIosHint, setShowIosHint] = useState(false)
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem('pwa-install-dismissed') === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    if (isStandalone() || dismissed) return

    const onBeforeInstall = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
    }

    window.addEventListener('beforeinstallprompt', onBeforeInstall)
    if (isIosSafari()) setShowIosHint(true)

    return () => window.removeEventListener('beforeinstallprompt', onBeforeInstall)
  }, [dismissed])

  const dismiss = () => {
    setDismissed(true)
    setDeferredPrompt(null)
    setShowIosHint(false)
    try {
      sessionStorage.setItem('pwa-install-dismissed', '1')
    } catch {
      /* ignore */
    }
  }

  const install = async () => {
    if (!deferredPrompt) return
    await deferredPrompt.prompt()
    await deferredPrompt.userChoice
    dismiss()
  }

  if (dismissed || isStandalone()) return null
  if (import.meta.env.DEV) return null
  if (!deferredPrompt && !showIosHint) return null

  return (
    <div className="fixed bottom-[calc(4.75rem+env(safe-area-inset-bottom))] left-4 right-4 z-[60] mx-auto max-w-md animate-slide-up md:bottom-4 md:left-auto md:right-4">
      <div className="flex items-start gap-3 rounded-2xl border border-brand-200/80 bg-white p-4 shadow-lg ring-1 ring-black/5 dark:border-brand-800 dark:bg-slate-800 dark:ring-white/10">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-brand text-white">
          <Download className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            {t.pwa.installTitle}
          </p>
          <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
            {showIosHint && !deferredPrompt ? t.pwa.installIosHint : t.pwa.installHint}
          </p>
          {showIosHint && !deferredPrompt && (
            <p className="mt-2 flex items-center gap-1.5 text-xs font-medium text-brand-600 dark:text-brand-400">
              <Share className="h-3.5 w-3.5" />
              {t.pwa.installIosSteps}
            </p>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            {deferredPrompt && (
              <button type="button" className="btn-primary btn-sm" onClick={() => void install()}>
                {t.pwa.installAction}
              </button>
            )}
            <button type="button" className="btn-secondary btn-sm" onClick={dismiss}>
              {t.pwa.dismiss}
            </button>
          </div>
        </div>
        <button
          type="button"
          className="shrink-0 rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700"
          aria-label={t.pwa.dismiss}
          onClick={dismiss}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
