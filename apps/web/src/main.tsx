import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import './monitor.css'
import './command-room.css'
import './room-overrides.css'
import './voice.css'
import './pwa.css'
import { InstallPrompt } from './InstallPrompt'

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    void navigator.serviceWorker.register('/service-worker.js').catch(() => undefined)
  })
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /><InstallPrompt /></StrictMode>)
