/**
 * PWA is production-only. In dev, tear down any leftover SW/caches so Vite is never blocked.
 */

async function disablePwaInDev(): Promise<void> {
  if (!import.meta.env.DEV) return

  if ('serviceWorker' in navigator) {
    const registrations = await navigator.serviceWorker.getRegistrations()
    await Promise.all(registrations.map((r) => r.unregister()))
    if (registrations.length > 0) {
      console.info(`[PWA] Dev mode — unregistered ${registrations.length} service worker(s)`)
    }
  }

  if ('caches' in window) {
    const keys = await caches.keys()
    await Promise.all(keys.map((key) => caches.delete(key)))
    if (keys.length > 0) {
      console.info(`[PWA] Dev mode — cleared ${keys.length} cache(s)`)
    }
  }
}

if (import.meta.env.PROD) {
  import('virtual:pwa-register').then(({ registerSW }) => {
    registerSW({
      immediate: true,
      onRegisterError(error) {
        console.warn('[PWA] Service worker registration failed:', error)
      },
    })
  })
} else {
  void disablePwaInDev()
}
