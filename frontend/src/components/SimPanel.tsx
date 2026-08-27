import { useState } from 'react'
import { api, type SystemStatus } from '../api'

type Action = {
  label: string
  desc: string
  tone: string
  fn: () => Promise<unknown>
}

const TONE: Record<string, string> = {
  primary: 'border-cyan-700 bg-cyan-950/50 text-cyan-300 hover:bg-cyan-900/50',
  danger: 'border-red-800 bg-red-950/40 text-red-300 hover:bg-red-900/50',
  warn: 'border-amber-700 bg-amber-950/40 text-amber-300 hover:bg-amber-900/50',
  neutral: 'border-slate-800 bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200',
  good: 'border-emerald-800 bg-emerald-950/40 text-emerald-300 hover:bg-emerald-900/50',
}

export default function SimPanel({
  status,
  role,
  onRefresh,
}: {
  status: SystemStatus | null
  role: string
  onRefresh: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [log, setLog] = useState<string[]>([])
  const isOperator = role === 'ADMIN' || role === 'COMMANDER'

  const push = (msg: string) => setLog((l) => [msg, ...l].slice(0, 30))

  const run = async (label: string, fn: () => Promise<unknown>) => {
    if (!isOperator) return
    setBusy(true)
    try {
      const res = (await fn()) as { message?: string; counts?: Record<string, number> }
      push(`✔ ${label}: ${res.message ?? JSON.stringify(res.counts ?? '')}`)
      onRefresh()
    } catch (e) {
      push(`✘ ${label}: ${(e as Error).message}`)
    } finally {
      setBusy(false)
    }
  }

  const actions: Action[] = [
    { label: 'Killer scenario', desc: 'Replay the flood demo — 80+ reports, deterministic seed 42', tone: 'primary', fn: () => api.simStart() },
    { label: 'Reset demo state', desc: 'Wipe all data back to an empty monitoring screen', tone: 'danger', fn: () => api.simReset() },
    { label: 'Step', desc: 'Advance the scenario one batch at a time', tone: 'neutral', fn: () => api.simStep() },
    { label: 'Inject fake SOS', desc: '500 fake SOS from one spot — watch confidence drop', tone: 'danger', fn: () => api.simInject('fake_sos') },
    { label: 'Inject duplicates', desc: '30 duplicates from one device — counted as one source', tone: 'warn', fn: () => api.simInject('duplicates') },
    { label: 'Net: normal', desc: 'Restore cellular — all uplinks open', tone: 'neutral', fn: () => api.simNetwork('NORMAL') },
    { label: 'Net: degraded', desc: 'Cellular congested — reports process slower', tone: 'warn', fn: () => api.simNetwork('DEGRADED') },
    { label: 'Net: cutout', desc: 'Cellular down — only SMS uplinks accepted', tone: 'danger', fn: () => api.simNetwork('CELLULAR_UNAVAILABLE') },
    { label: 'LLM: kill', desc: 'Turn off AI enrichment — rules-only fallback', tone: 'danger', fn: () => api.simLlm(false) },
    { label: 'LLM: restore', desc: 'Bring AI enrichment back online', tone: 'good', fn: () => api.simLlm(true) },
  ]

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-3">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold tracking-widest text-slate-400 uppercase">Simulation</span>
        <span className="text-[10px] text-slate-500">{status?.connectivity_mode}</span>
      </div>
      <div className="mt-2 space-y-1.5">
        {actions.map((a) => (
          <button
            key={a.label}
            disabled={busy || !isOperator}
            onClick={() => run(a.label, a.fn)}
            className={`w-full rounded border px-2 py-1.5 text-left text-xs disabled:opacity-40 ${TONE[a.tone]}`}
          >
            <span className="font-medium">{a.label}</span>
            <span className="block text-[10px] font-normal opacity-70">{a.desc}</span>
          </button>
        ))}
      </div>
      {!isOperator && (
        <div className="mt-2 text-[10px] text-slate-500">Simulation controls require ADMIN/COMMANDER.</div>
      )}
      {log.length > 0 && (
        <div className="mt-2 space-y-0.5">
          {log.map((line, i) => (
            <div key={i} className="font-mono text-[10px] text-slate-500">
              {line}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}