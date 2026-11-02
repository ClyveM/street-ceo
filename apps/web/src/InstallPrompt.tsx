import { useEffect, useState } from 'react'

type InstallPromptEvent = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }> }

export function InstallPrompt() {
  const [installEvent, setInstallEvent] = useState<InstallPromptEvent | null>(null)
  const [installed, setInstalled] = useState(false)
  const [secure, setSecure] = useState(true)
  const [helpDismissed, setHelpDismissed] = useState(false)

  useEffect(() => {
    setSecure(window.isSecureContext)
    const onPrompt = (event: Event) => { event.preventDefault(); setInstallEvent(event as InstallPromptEvent) }
    const onInstalled = () => { setInstalled(true); setInstallEvent(null) }
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => { window.removeEventListener('beforeinstallprompt', onPrompt); window.removeEventListener('appinstalled', onInstalled) }
  }, [])

  if (installed) return <div className="install-note" role="status">✓ Street CEO is installed on this device.</div>
  if (!secure && !helpDismissed) return <div className="install-card install-help" role="status"><div><strong>Install is blocked on this phone address</strong><span>Phone installation needs HTTPS. Use an HTTPS link, then open Chrome’s menu and choose “Install app” or “Add to Home screen”.</span></div><button className="install-dismiss" aria-label="Dismiss install help" onClick={() => setHelpDismissed(true)}>×</button></div>
  if (!installEvent) return null
  const install = async () => { await installEvent.prompt(); const choice = await installEvent.userChoice; if (choice.outcome === 'accepted') setInstalled(true); setInstallEvent(null) }
  return <div className="install-card" role="status"><div><strong>Take Street CEO with you</strong><span>Install the shop dashboard for quick access.</span></div><button onClick={() => void install}>Install app</button><button className="install-dismiss" aria-label="Dismiss install prompt" onClick={() => setInstallEvent(null)}>×</button></div>
}
