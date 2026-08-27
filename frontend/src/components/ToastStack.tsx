import type { Incident } from '../api'

export interface ZoneLite {
  zone_id: string
  priority: string
  incident_count: number
  source_count: number
}

export interface Toast {
  id: number
  title: string
  detail: string
  tone: 'red' | 'amber' | 'cyan'
}

const RANK: Record<string, number> = { P1: 3, P2: 2, P3: 1, P4: 0, UNRATED: -1 }

export function diffToasts(
  prevInc: Map<string, string>,
  currInc: Incident[],
  prevZone: Map<string, string>,
  currZones: ZoneLite[],
): Toast[] {
  const out: Toast[] = []
  const id = (s: string) => s.slice(0, 8)
  for (const inc of currInc) {
    const prev = prevInc.get(inc.incident_id)
    if (prev === undefined) {
      out.push({
        id: Math.random(),
        title: `${inc.priority} · new incident`,
        detail: `${id(inc.incident_id)} · ${inc.severity} · ${inc.evidence_count} evidence · ${inc.independent_source_count} sources`,
        tone: inc.priority === 'P1' ? 'red' : 'cyan',
      })
    } else if (prev !== inc.priority && (RANK[inc.priority] ?? -1) > (RANK[prev] ?? -1)) {
      out.push({
        id: Math.random(),
        title: `${prev} → ${inc.priority} · escalated`,
        detail: `${id(inc.incident_id)} · ${inc.severity} · ${inc.evidence_count} evidence · ${inc.independent_source_count} sources`,
        tone: 'red',
      })
    }
  }
  for (const z of currZones) {
    const prev = prevZone.get(z.zone_id)
    if (prev === undefined && z.priority === 'P1') {
      out.push({
        id: Math.random(),
        title: `${z.priority} · zone formed`,
        detail: `${id(z.zone_id)} · ${z.incident_count} incidents · ${z.source_count} sources`,
        tone: 'red',
      })
    } else if (prev !== undefined && prev !== z.priority && (RANK[z.priority] ?? -1) > (RANK[prev] ?? -1)) {
      out.push({
        id: Math.random(),
        title: `zone ${prev} → ${z.priority} · escalated`,
        detail: `${id(z.zone_id)} · ${z.incident_count} incidents · ${z.source_count} sources`,
        tone: 'red',
      })
    }
  }
  return out
}

const TONE: Record<string, string> = {
  red: 'border-red-600/60 bg-red-950/80 text-red-200',
  amber: 'border-amber-600/60 bg-amber-950/80 text-amber-200',
  cyan: 'border-cyan-600/60 bg-cyan-950/80 text-cyan-200',
}

export default function ToastStack({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="pointer-events-none absolute top-2 right-2 z-50 flex w-80 flex-col gap-1.5">
      {toasts.map((t) => (
        <div key={t.id} className={`toast-enter rounded-lg border px-3 py-2 shadow-xl shadow-black/40 backdrop-blur ${TONE[t.tone]}`}>
          <div className="text-xs font-semibold tracking-wide uppercase">{t.title}</div>
          <div className="mt-0.5 font-mono text-[10px] opacity-80">{t.detail}</div>
        </div>
      ))}
    </div>
  )
}