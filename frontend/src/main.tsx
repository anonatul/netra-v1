import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import VictimApp from './victim/VictimApp.tsx'
import LogTerminal from './logs/LogTerminal.tsx'

const path = window.location.pathname
const isVictim = path.startsWith('/victim')
const isLogs = path.startsWith('/logs')

createRoot(document.getElementById('root')!).render(
  isVictim ? <VictimApp /> : isLogs ? <LogTerminal /> : <App />,
)