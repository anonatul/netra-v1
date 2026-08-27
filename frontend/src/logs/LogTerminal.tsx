import { useEffect, useRef, useState } from 'react'
import { BASE } from '../api'

type AuditEntry = {
  id: number
  user_id: number
  action: string
  target_type: string
  target_id: string
  previous_value?: unknown
  new_value?: unknown
  reason?: string
  timestamp: string
}

const ACTION_COLOR: Record<string, string> = {
  EVENT_INGESTED: 'text-emerald-300',
  PRIORITY_OVERRIDE: 'text-amber-300',
  RECOMMENDATION: 'text-cyan-300',
  FIELD_UPDATE: 'text-violet-300',
}

function fmtTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function detail(e: AuditEntry): string {
  let v = ''
  if (typeof e.new_value === 'string') v = e.new_value
  else if (e.new_value) v = JSON.stringify(e.new_value)
  return `${e.target_type}#${e.target_id}${v ? ' · ' + v : ''}${e.reason ? ' · ' + e.reason : ''}`
}

export default function LogTerminal() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('netra_log_token'))
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [lines, setLines] = useState<AuditEntry[]>([])
  const seenRef = useRef<Set<number>>(new Set())
  const [status, setStatus] = useState<string>('connecting…')
  const [forbidden, setForbidden] = useState(false)

  const login = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setErr(null)
    try {
      const res = await fetch(`${BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const body = await res.json()
      if (!res.ok) throw new Error(body.detail?.message || `${res.status}`)
      localStorage.setItem('netra_log_token', body.access_token)
      setToken(body.access_token)
    } catch (er) {
      setErr((er as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const signOut = () => {
    localStorage.removeItem('netra_log_token')
    setToken(null)
    setLines([])
    setForbidden(false)
  }

  useEffect(() => {
    if (!token) return
    const poll = async () => {
      try {
        const res = await fetch(`${BASE}/audit?limit=40`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.status === 403) {
          setForbidden(true)
          setStatus('FORBIDDEN — need AUDITOR/ADMIN role')
          return
        }
        if (!res.ok) throw new Error(`${res.status}`)
        setForbidden(false)
        const data = await res.json()
        const fresh = (data.entries ?? []).filter((e: AuditEntry) => !seenRef.current.has(e.id))
        fresh.forEach((e: AuditEntry) => seenRef.current.add(e.id))
        if (fresh.length > 0) setLines((prev) => [...prev, ...fresh].slice(0, 60))
        setStatus(`live · ${data.count} events`)
      } catch {
        setStatus('offline')
      }
    }
    poll()
    const t = setInterval(poll, 2000)
    return () => clearInterval(t)
  }, [token])

  if (!token) {
    return (
      <div className="log-term flex min-h-screen items-center justify-center px-6">
        <form onSubmit={login} className="w-80 border border-slate-800 bg-black/40 p-6">
          <div className="font-mono text-sm text-emerald-300">
            netra@ops:~$ <span className="text-slate-400">authenticate</span>
          </div>
          <label className="mt-5 block font-mono text-[10px] tracking-widest text-slate-600 uppercase">Username</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 w-full border border-slate-800 bg-[#0a120c] px-2.5 py-2 font-mono text-sm text-emerald-200 outline-none focus:border-emerald-600"
          />
          <label className="mt-3 block font-mono text-[10px] tracking-widest text-slate-600 uppercase">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full border border-slate-800 bg-[#0a120c] px-2.5 py-2 font-mono text-sm text-emerald-200 outline-none focus:border-emerald-600"
          />
          {err && <div className="mt-3 font-mono text-xs text-red-400">{err}</div>}
          <button
            disabled={busy}
            className="mt-5 w-full border border-emerald-700 bg-emerald-950/40 py-2 font-mono text-xs tracking-widest text-emerald-300 hover:bg-emerald-900/50 disabled:opacity-40"
          >
            CONNECT
          </button>
          <div className="mt-4 font-mono text-[10px] text-slate-600">admin / admin123 · auditor / auditor123</div>
        </form>
      </div>
    )
  }

  return (
    <div className="log-term relative flex min-h-screen flex-col bg-[#050a07] font-mono text-emerald-300">
      <div className="flex items-center justify-between border-b border-slate-800 bg-black/40 px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </span>
          <span className="text-[11px] tracking-widest text-emerald-300">NETRA · SYSTEM LOG</span>
        </div>
        <div className="flex items-center gap-4">
          <span className={`text-[10px] ${forbidden ? 'text-red-400' : 'text-slate-500'}`}>{status}</span>
          <button onClick={signOut} className="text-[10px] tracking-widest text-slate-500 hover:text-amber-300">
            ↺ re-auth
          </button>
          <a href="#/" className="text-[10px] tracking-widest text-slate-500 hover:text-emerald-300">
            ← dashboard
          </a>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {forbidden && (
          <div className="mb-3 border border-red-900 bg-red-950/40 px-3 py-2 text-[12px] text-red-300">
            ACCESS DENIED — audit trail needs an AUDITOR or ADMIN account.{' '}
            <button onClick={signOut} className="underline underline-offset-2 hover:text-red-100">
              Sign in as admin
            </button>
          </div>
        )}
        {lines.length === 0 && !forbidden && (
          <div className="text-[12px] text-slate-600">waiting for log entries…</div>
        )}
        {lines.map((e) => (
          <div key={e.id} className="whitespace-pre-wrap break-all py-0.5 text-[12px] leading-relaxed">
            <span className="text-slate-600">[{fmtTime(e.timestamp)}]</span>{' '}
            <span className={ACTION_COLOR[e.action] ?? 'text-slate-300'}>{e.action}</span>{' '}
            <span className="text-slate-500">{detail(e)}</span>
          </div>
        ))}
        <div className="mt-1 text-[12px]">
          <span className="text-emerald-400">netra@ops:~$</span>
          <span className="log-cursor ml-2 text-emerald-400" />
        </div>
      </div>
      <div className="log-scanlines pointer-events-none fixed inset-0" />
    </div>
  )
}