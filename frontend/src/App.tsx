import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type Incident, type MapData, type SystemStatus } from './api'
import NetraMap from './components/NetraMap'
import IncidentList from './components/IncidentList'
import DetailPanel from './components/DetailPanel'
import SimPanel from './components/SimPanel'
import StatusBar from './components/StatusBar'
import LiveReportPanel from './components/LiveReportPanel'
import SituationStrip from './components/SituationStrip'
import SignalStream from './components/SignalStream'
import ToastStack, { diffToasts, type Toast } from './components/ToastStack'

const isSimPath = () =>
  typeof window !== 'undefined' && window.location.hash.replace(/^#\/?/, '') === 'sim'

function Login({ onLogin }: { onLogin: (role: string, name: string) => void }) {
  const [username, setUsername] = useState('commander')
  const [password, setPassword] = useState('commander123')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const isSim = isSimPath()

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const res = await api.login(username, password)
      localStorage.setItem('netra_token', res.access_token)
      onLogin(res.user.role, res.user.display_name)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="netra-login flex min-h-screen items-center justify-center">
      <form
        onSubmit={submit}
        className="netra-login-card w-80 rounded-xl border p-6"
      >
        <div className="text-center">
          <div className="font-display text-3xl font-bold tracking-[0.3em] text-slate-900">NETRA</div>
          <div className="mt-1 text-[10px] tracking-widest text-slate-500">
            NETWORK-RESILIENT EMERGENCY TRIAGE &amp; RESPONSE
          </div>
        </div>
        <label className="mt-6 block text-xs text-slate-400">Username</label>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mt-1 w-full rounded border border-slate-700 bg-[#0f1513] px-2.5 py-2 text-sm text-slate-200 outline-none focus:border-red-700"
        />
        <label className="mt-3 block text-xs text-slate-400">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 w-full rounded border border-slate-700 bg-[#0f1513] px-2.5 py-2 text-sm text-slate-200 outline-none focus:border-red-700"
        />
        {error && <div className="mt-3 text-xs text-red-400">{error}</div>}
        <button
          disabled={busy}
          className="mt-5 w-full rounded bg-[#e0e0e0] py-2 text-sm font-semibold text-[#0b0b0b] hover:bg-[#c8c8c8] disabled:opacity-50"
        >
          Sign in
        </button>
        {isSim && (
          <div className="mt-4 text-center text-[10px] text-slate-600">
            demo: commander / commander123 · operator / operator123 · auditor / auditor123
          </div>
        )}
      </form>
    </div>
  )
}

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('netra_token'))
  const [user, setUser] = useState<{ name: string; role: string } | null>(null)
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [mapData, setMapData] = useState<MapData | null>(null)
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [toasts, setToasts] = useState<Toast[]>([])
  const prevIncRef = useRef<Map<string, string>>(new Map())
  const prevZoneRef = useRef<Map<string, string>>(new Map())
  const isSim = isSimPath()

  const pushToasts = (items: Toast[]) => {
    if (items.length === 0) return
    setToasts((prev) => [...items, ...prev].slice(0, 6))
    items.forEach((t) => {
      setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== t.id)), 6000)
    })
  }

  const refresh = useCallback(async () => {
    try {
      const [s, m, i] = await Promise.all([api.status(), api.mapData(), api.incidents()])
      setStatus(s)
      setMapData(m)
      setIncidents(i)
      const newToasts = diffToasts(prevIncRef.current, i, prevZoneRef.current, m.zones)
      prevIncRef.current = new Map(i.map((x) => [x.incident_id, x.priority]))
      prevZoneRef.current = new Map(m.zones.map((z) => [z.zone_id, z.priority]))
      pushToasts(newToasts)
    } catch {
      /* polling will retry */
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!token) return
    refresh()
    const t = setInterval(refresh, 4000)
    return () => clearInterval(t)
  }, [token, refresh])

  useEffect(() => {
    if (!token) return
    api.me().then((u) => setUser({ name: u.display_name, role: u.role })).catch(() => {})
  }, [token])

  useEffect(() => {
    if (isSim && token) api.status().then(setStatus).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSim, token])

  const selected = incidents.find((i) => i.incident_id === selectedId) ?? null

  if (!token) {
    return (
      <Login
        onLogin={(role, name) => {
          setUser({ role, name })
          setToken(localStorage.getItem('netra_token'))
        }}
      />
    )
  }

  const canCommand = user?.role === 'ADMIN' || user?.role === 'COMMANDER'

  if (isSim) {
    return (
      <div className="netra-dash flex min-h-screen items-start justify-center bg-[#070b16] px-4 py-8 text-slate-200">
        <div className="w-full max-w-md">
          <div className="mb-4 flex items-baseline justify-between">
            <span className="font-display text-lg font-bold tracking-[0.3em] text-cyan-400">NETRA</span>
            <div className="flex items-center gap-3 font-mono text-[10px]">
              <a href="#/logs" className="text-slate-500 hover:text-emerald-300">
                system log →
              </a>
              <a href="#/" className="text-slate-500 hover:text-slate-300">
                ← open dashboard
              </a>
            </div>
          </div>
          <SimPanel status={status} role={user?.role ?? ''} onRefresh={() => {}} />
          <div className="mt-3">
            <LiveReportPanel onRefresh={() => {}} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="netra-dash relative flex h-screen flex-col bg-[#111514] text-slate-200">
      <StatusBar
        status={status}
        userName={user?.name ?? '—'}
        role={user?.role ?? '—'}
        onLogout={() => {
          localStorage.removeItem('netra_token')
          setToken(null)
          setUser(null)
        }}
      />
      <div className="netra-rule" />
      <SituationStrip status={status} incidents={incidents} mapData={mapData} />
      <div className="grid min-h-0 flex-1 grid-rows-1 grid-cols-[280px_1fr_340px]">
        <aside className="flex flex-col border-r border-slate-800 bg-slate-950/60">
          <div className="min-h-0 flex-1 overflow-y-auto">
            <IncidentList incidents={incidents} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
          {isSim && (
            <div className="border-t border-slate-800 p-2">
              <SimPanel status={status} role={user?.role ?? ''} onRefresh={refresh} />
            </div>
          )}
          {isSim && <LiveReportPanel onRefresh={refresh} />}
        </aside>
        <main className="relative min-h-0">
          <NetraMap data={mapData} selectedId={selectedId} onSelect={setSelectedId} />
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-[#070b16]/80 text-xs text-slate-500">
              connecting to NETRA backend…
            </div>
          )}
          {mapData && mapData.zones.length === 0 && mapData.incidents.length === 0 && !loading && (
            <div className="pointer-events-none absolute bottom-3 left-1/2 -translate-x-1/2 rounded bg-slate-950/85 px-3 py-1.5 text-[11px] text-slate-400">
              Standing by — no active field reports.
            </div>
          )}
        </main>
        <aside className="min-h-0 overflow-y-auto border-l border-slate-800 bg-slate-950/60">
          <DetailPanel
            incident={selected}
            canCommand={canCommand}
            onClose={() => setSelectedId(null)}
            onRefresh={refresh}
          />
        </aside>
      </div>
      <SignalStream />
      <ToastStack toasts={toasts} />
      <div className="netra-scanlines" />
    </div>
  )
}