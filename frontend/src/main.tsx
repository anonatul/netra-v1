import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import VictimApp from './victim/VictimApp.tsx'
import LogTerminal from './logs/LogTerminal.tsx'

const route = window.location.hash.replace(/^#\/?/, '')
const isVictim = route.startsWith('victim')
const isLogs = route.startsWith('logs')

createRoot(document.getElementById('root')!).render(
  isVictim ? <VictimApp /> : isLogs ? <LogTerminal /> : <App />,
)