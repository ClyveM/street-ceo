import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'
import './monitor.css'
import './command-room.css'
import './room-overrides.css'
import './voice.css'

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
