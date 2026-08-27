import type { SystemStatus } from '../api'

const MODE_COLOR: Record<string, string> = {
  ONLINE: 'bg-emerald-500',
  SATCOM: 'bg-amber-500',
  DEGRADED: 'bg-orange-500',
  OFFLINE: 'bg-red-500',
}

export default function StatusBar({
  status,
  userName,
  role,
  onLogout,
}: {
  status: SystemStatus | null
  userName: string
  role: string
  onLogout: () => void
}) {
  const llm = status?.llm_health
  return (
    <div className="flex items-center gap-4 border-b border-slate-800 bg-slate-950 px-4 py-2 text-xs">
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1.5 rounded border border-emerald-700/60 bg-emerald-950/40 px-1.5 py-0.5">
          <span className={`h-1.5 w-1.5 rounded-full bg-emerald-400 ${status ? 'animate-live-pulse' : ''}`} />
          <span className="font-mono text-[9px] font-medium tracking-widest text-emerald-300">LIVE</span>
        </span>
        <span className="font-display text-xl font-bold tracking-[0.3em] text-cyan-400">NETRA</span>
        <span className="hidden text-[10px] text-slate-500 md:inline">
          NETWORK-RESILIENT EMERGENCY TRIAGE &amp; RESPONSE
        </span>
      </div>

      <div className="ml-auto flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className={`h-2 w-2 rounded-full ${MODE_COLOR[status?.connectivity_mode ?? 'OFFLINE'] ?? MODE_COLOR.OFFLINE}`} />
          <span className="text-slate-300">{status?.connectivity_mode ?? 'OFFLINE'}</span>
        </div>
        <div className="flex items-center gap-1.5" title={status?.llm_last_error ?? ''}>
          <span
            className={`h-2 w-2 rounded-full ${llm === 'HEALTHY' ? 'bg-emerald-500' : llm === 'DEGRADED' ? 'bg-amber-500' : 'bg-slate-600'}`}
          />
          <span className="text-slate-300">L3 LLM {llm ?? '…'}</span>
          {status?.llm_last_latency_ms != null && (
            <span className="text-slate-500">{status.llm_last_latency_ms}ms</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-slate-400">
          <span>{status?.total_events ?? 0} events</span>
          <span>{status?.total_incidents ?? 0} incidents</span>
          <span>{status?.open_incidents ?? 0} open</span>
          {status?.disaster_active && <span className="text-amber-400">{status.disaster_active}</span>}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-300">
            {userName} <span className="text-[10px] text-slate-500">({role})</span>
          </span>
          <button onClick={onLogout} className="rounded border border-slate-700 px-2 py-0.5 text-slate-400 hover:bg-slate-800">
            logout
          </button>
        </div>
      </div>
    </div>
  )
}