import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import './brand-logo.css'
import './voice.css'
import './pwa.css'
import './pwa-help.css'
import './business-navigation.css'
import './emerald-ux.css'

// Street CEO installs through the APK; keep browser install promotion out of the UI.
window.addEventListener('beforeinstallprompt', (event) => event.preventDefault())

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    void navigator.serviceWorker.register('/service-worker.js', { updateViaCache: 'none' }).then((registration) => registration.update()).catch(() => undefined)
  })
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
