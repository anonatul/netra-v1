import { PRIORITY_COLOR } from './NetraMap'
import type { Incident } from '../api'

const VULN_LABELS: Record<string, string> = {
  elderly: 'Elderly',
  child: 'Child',
  pregnant: 'Pregnant',
  mobility_issue: 'Mobility-impaired',
  medical_critical: 'Medical critical',
  trapped: 'Trapped',
}

export default function IncidentList({
  incidents,
  selectedId,
  onSelect,
}: {
  incidents: Incident[]
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const sorted = [...incidents].sort((a, b) => {
    const rank = { P1: 0, P2: 1, P3: 2, P4: 3, UNRATED: 4 }
    return (rank[a.priority] ?? 5) - (rank[b.priority] ?? 5)
  })

  return (
    <div className="flex flex-col gap-1.5 overflow-y-auto p-2">
      <div className="px-1 pb-1 text-[11px] font-semibold tracking-widest text-slate-400 uppercase">
        Incidents · {sorted.length}
      </div>
      {sorted.map((inc) => {
        const vulns = Object.entries(inc.vulnerability ?? {})
          .filter(([, v]) => v)
          .map(([k]) => VULN_LABELS[k] ?? k)
        const color = PRIORITY_COLOR[inc.priority] ?? PRIORITY_COLOR.UNRATED
        const selected = inc.incident_id === selectedId
        return (
          <button
            key={inc.incident_id}
            onClick={() => onSelect(inc.incident_id)}
            style={{ borderLeft: `3px solid ${color}` }}
            className={`rounded-sm border border-slate-800 px-2.5 py-2 text-left transition-colors ${
              selected
                ? 'bg-slate-800/80'
                : 'bg-slate-950/70 hover:bg-slate-900'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-[11px] text-slate-300">{inc.incident_id}</span>
              <span
                className="rounded px-1.5 py-0.5 text-[10px] font-bold text-white"
                style={{ backgroundColor: color }}
              >
                {inc.priority}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                {inc.severity} · conf {inc.confidence != null ? Math.round(inc.confidence * 100) : '?'}%
              </span>
              <span className="text-[11px] text-slate-400">~{inc.victim_estimate ?? '?'} victims</span>
            </div>
            {inc.location.lat === null && (
              <div className="mt-1">
                <span className="rounded bg-amber-950/60 px-1.5 py-0.5 font-mono text-[9px] text-amber-300">
                  UNLOCATED — awaiting GPS
                </span>
              </div>
            )}
            <div className="mt-1 flex flex-wrap gap-1">
              {vulns.slice(0, 3).map((v) => (
                <span key={v} className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-cyan-300">
                  {v}
                </span>
              ))}
              {inc.zone_id && (
                <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">
                  zone {inc.zone_id.slice(0, 6)}
                </span>
              )}
            </div>
            <div className="mt-1 text-[10px] text-slate-500">
              {inc.evidence_count} evidence · {inc.independent_source_count} sources
            </div>
          </button>
        )
      })}
      {sorted.length === 0 && (
        <div className="px-2 py-6 text-center text-xs text-slate-500">No active incidents</div>
      )}
    </div>
  )
}